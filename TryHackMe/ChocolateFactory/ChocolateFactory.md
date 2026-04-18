# 🛡️ TryHackMe – Chocolate Factory - Writeup

## 📌 Overview
**Room Name:** Chocolate Factory  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Steganography / Hash Cracking / Privilege Escalation / Cryptography

Linux machine featuring anonymous FTP, steganography to extract a shadow hash, and a sudo `vi` shell escape, with a final Fernet decryption challenge.

The attack chain involves:

- Anonymous FTP access to retrieve a steganographic image
- steghide to extract `/etc/shadow` hash from the image
- hashcat to crack charlie's password hash
- SSH private key (`teleport`) discovery for stable SSH access
- sudo `vi` shell escape for root access
- Fernet key extraction and decryption to retrieve the root flag

---

## 🔍 1. Enumeration

### 🔎 Port Scanning
`nmap` SYN stealth scan revealed a large number of open ports. The most relevant for the attack path:

```text
21/tcp  open  ftp
22/tcp  open  ssh
80/tcp  open  http
```

Although many ports were open, FTP, SSH, and HTTP were prioritized as the most likely attack surface.

### 🌐 Web Investigation
Browsing to port 80 revealed a **login page** submitting credentials to `validate.php`. SQL Injection was tested but did not appear to be viable, so focus shifted to FTP.

### 📂 Anonymous FTP
Anonymous login was enabled with no password required. Retrieved:

- `gum_room.jpg` — downloaded for steganographic analysis

---

## 🔓 2. Initial Access

### 🖼️ Steganography & Shadow Hash Extraction
Inspected `gum_room.jpg` with `steghide`, which revealed embedded content containing the `/etc/shadow` file. Extracted hash for user `charlie`:

```text
charlie:$6$CZJnCPeQWp9/jpNx$khGlFdICJnr8R3JC/jTR2r7DrbFLp8zq8469d3c0.zuKN4se61FObwWGxcHZqO2RJHkkL1jjPYeeGyIJWE82X/
```

The `$6$` prefix indicates **SHA-512 crypt**.

### 🔑 Hash Cracking
Used `hashcat` to crack the extracted hash:

- **Username:** `charlie`
- **Recovered Password:** `[REDACTED]`

### 🔐 SSH Access via RSA Key
Using the cracked credentials resulted in access as `www-data`. Enumerating `/home/charlie` revealed a file named `teleport` — an **RSA private key**.

Used the key to SSH in as `charlie`:

```bash
ssh -i teleport charlie@<target_ip>
whoami
# charlie
```

**Initial access as `charlie` achieved.** ✅

---

## 👑 3. Privilege Escalation: charlie → root

### ⚠️ Sudo Misconfiguration — vi Shell Escape
Checked sudo permissions:

```bash
sudo -l
```

```text
(ALL : !root) NOPASSWD: /usr/bin/vi
```

Although `!root` looks restrictive, `vi` supports **shell escape**, making it dangerous in any sudo context. Escaped to a root shell from within `vi`:

```
:!/bin/bash
```

**ROOT ACCESS GRANTED.** ✅

### 🔐 Fernet Decryption
As root, found `root.py` — a script using the `cryptography.fernet` module. The Fernet key was embedded in a binary at `/var/www/html/key_rev_key`:

```text
-VkgXhFf6sAEcAwrC6YR-SZbiuSb8ABXeQuvhcGSQzY=
```

Used the key to decrypt the encrypted token in `root.py` and recovered the root flag.

---

## 📚 Key Takeaways

- 📂 **Anonymous FTP can bypass harder attack surfaces:** Sensitive files exposed via FTP can be more damaging than complex web vulnerabilities.
- 🖼️ **Steganography hides more than images:** `/etc/shadow` embedded in a JPEG — always analyze files from FTP and web servers thoroughly.
- 🔑 **SSH keys found on compromised hosts are gold:** The `teleport` key provided stable access without needing to crack credentials directly via SSH.
- 🐚 **`vi` in sudo is dangerous:** Shell escape features in editors like `vi`, `nano`, and `less` make them highly exploitable when granted sudo rights.
- 🔐 **Final flags may require decryption:** Not all root access ends with `cat root.txt` — binary analysis and cryptography can be part of the chain.

---

## 🛠️ Tools Used

- `nmap`
- `steghide`
- `hashcat`
- `ssh`
- `vi` (shell escape)

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
