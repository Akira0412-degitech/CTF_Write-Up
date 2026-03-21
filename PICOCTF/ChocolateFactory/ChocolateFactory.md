# 🛡️ TryHackMe – Chocolate Factory - Writeup

## 📌 Overview
**Room Name:** Chocolate Factory  
**Platform:** TryHackMe  
**Difficulty:** Easy

Chocolate Factory is a beginner-friendly CTF machine that covers several core penetration testing concepts, including service enumeration, anonymous FTP access, steganography, password hash cracking, SSH key abuse, sudo misconfiguration, and final-stage decryption using a Fernet key.

---

## 🔍 1. Enumeration
### Port Scanning
I began with an `nmap` SYN stealth scan against the target and identified a large number of open ports. The most relevant ones for the attack path were:

- **21/tcp (FTP)** – file transfer service
- **22/tcp (SSH)** – remote login service
- **80/tcp (HTTP)** – web application

Example scan output:

```text
Initiating SYN Stealth Scan at 12:27
Scanning 10.49.141.204 [29 ports]
Discovered open port 110/tcp on 10.49.141.204
Discovered open port 111/tcp on 10.49.141.204
Discovered open port 22/tcp on 10.49.141.204
Discovered open port 80/tcp on 10.49.141.204
Discovered open port 21/tcp on 10.49.141.204
Discovered open port 113/tcp on 10.49.141.204
Discovered open port 122/tcp on 10.49.141.204
Discovered open port 125/tcp on 10.49.141.204
Discovered open port 112/tcp on 10.49.141.204
Discovered open port 108/tcp on 10.49.141.204
Discovered open port 114/tcp on 10.49.141.204
Discovered open port 103/tcp on 10.49.141.204
Discovered open port 109/tcp on 10.49.141.204
Discovered open port 117/tcp on 10.49.141.204
Discovered open port 105/tcp on 10.49.141.204
Discovered open port 124/tcp on 10.49.141.204
Discovered open port 101/tcp on 10.49.141.204
Discovered open port 119/tcp on 10.49.141.204
Discovered open port 116/tcp on 10.49.141.204
Discovered open port 102/tcp on 10.49.141.204
Discovered open port 115/tcp on 10.49.141.204
Discovered open port 107/tcp on 10.49.141.204
Discovered open port 123/tcp on 10.49.141.204
Discovered open port 118/tcp on 10.49.141.204
Discovered open port 106/tcp on 10.49.141.204
Discovered open port 121/tcp on 10.49.141.204
Discovered open port 120/tcp on 10.49.141.204
Discovered open port 104/tcp on 10.49.141.204
Discovered open port 100/tcp on 10.49.141.204
```

Although many ports were open, I prioritized **FTP, SSH, and HTTP** because they were the most likely to provide a practical foothold.

---

## 🌐 2. Web Investigation
Browsing to port 80 revealed a **login page**. The form submitted credentials to `validate.php`.

I tested the login flow and explored the possibility of **SQL Injection**, but based on the responses and behavior, it did **not appear to be vulnerable**. Since the web route did not immediately lead to access, I shifted focus to the other exposed services.

---

## 📂 3. FTP Enumeration and File Retrieval
Connecting to the FTP service showed that **anonymous login** was enabled and **no password was required**.

After logging in, I found an interesting file:

- `gum_room.jpg`

I downloaded this image for further analysis, suspecting that it might contain hidden data.

---

## 🖼️ 4. Steganography and Hidden Data Extraction
I inspected `gum_room.jpg` using `steghide` and found embedded content inside the image. After extracting the hidden file and decoding it, I obtained the contents of `/etc/shadow`.

This revealed a valid password hash for the user `charlie`:

```text
charlie:$6$CZJnCPeQWp9/jpNx$khGlFdICJnr8R3JC/jTR2r7DrbFLp8zq8469d3c0.zuKN4se61FObwWGxcHZqO2RJHkkL1jjPYeeGyIJWE82X/:
```

The `$6$` prefix indicated that this was a **SHA-512 crypt** hash.

---

## 🔓 5. Hash Cracking
I used `hashcat` to crack the extracted password hash for `charlie`.

- **Username:** `charlie`
- **Recovered Password:** `[REDACTED]`

This gave me valid credentials to continue the attack chain.

---

## 🧪 6. Initial Access and Pivot to Charlie
After using the discovered credentials, I ended up with access as **`www-data`**.

From there, I enumerated the filesystem and inspected `/home/charlie`, where I found a suspicious file:

- `teleport`

Upon viewing its content, I confirmed that it was an **RSA private key**.

I then used this private key to authenticate via SSH, which gave me an interactive shell as `charlie`.

Verification:

```bash
whoami
charlie
```

At this stage, I retrieved the user flag:

---

## 🚀 7. Privilege Escalation: charlie → root
Next, I checked Charlie’s sudo permissions:

```bash
sudo -l
```

The result showed that `charlie` could run:

```text
(ALL : !root) NOPASSWD: /usr/bin/vi
```

Although this looked restricted, `vi` supports **shell escape**, which makes it dangerous when allowed through sudo.

I exploited this misconfiguration by escaping to a shell from within `vi`, which resulted in **root access**.

This was the key privilege escalation step.

---

## 🔐 8. Root-Level Analysis and Fernet Decryption
As root, I found a Python script named:

- `root.py`

This script required a **key** and used the `cryptography.fernet` module to decrypt a token.

I then investigated another file:

- `/var/www/html/key_rev_key`

This was a binary, but when analyzed, it revealed the Fernet key:

```text
-VkgXhFf6sAEcAwrC6YR-SZbiuSb8ABXeQuvhcGSQzY=
```

After fixing `root.py` slightly so that it handled bytes correctly, I used the key to decrypt the encrypted message and recovered the root flag:

---

## 📚 Key Takeaways
- **Anonymous FTP** can expose sensitive files that completely bypass harder web attack surfaces.
- **Steganography** is often used in CTFs to hide credentials or hashes.
- Recovering `/etc/shadow` can be enough to pivot further through **password cracking**.
- **SSH private keys** found on a compromised host are often more useful than passwords.
- Allowing tools like **`vi` through sudo** is dangerous because of built-in shell escape features.
- Even after gaining root, final flags may require **binary analysis** or **decryption** instead of just reading a text file.