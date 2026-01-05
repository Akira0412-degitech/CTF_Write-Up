# 🛡️ TryHackMe – Cyborg
Full Technical Walkthrough & Detailed Write-up

  

---

## 📌 Overview
Room Name: Cyborg

Platform: TryHackMe

Difficulty: Easy

Category: Web / Archive Analysis / Privilege Escalation

This challenge involves a series of steps starting from web enumeration, hash cracking, and analyzing a Borg Backup repository, ultimately leading to root access via a command injection vulnerability in a custom script.

---

## 🔍 1. Enumeration Phase
### 🔎 Service Scanning

The initial reconnaissance was performed using `rustscan` to identify open ports on the target machine.

```

rustscan -a <TARGET_IP>

```

Results:

• 22/tcp: SSH

• 80/tcp: HTTP (Apache2 default page)

### 🌐 Web Directory Discovery

As the root page was a default Apache installation, `gobuster` was used to uncover hidden directories.

```

gobuster dir -u http://<TARGET_IP> -w /usr/share/wordlists/dirb/big.txt -x php -t 50

```

Key Findings:

• `/admin`: Contained a "Shoutbox" where a user named Alex mentioned insecure squid proxy settings.

• `/etc`: Revealed a `passwd` file containing a hash and a `squid.conf` configuration file.

---

## 🔓 2. Initial Access
### 🔑 Hash Cracking

The hash extracted from `/etc/passwd` was:

`music_archive:$apr1$BpZ.Q.1m$F0qqPwHSOG50URuOVQTTn.`

Using `hashcat` with the Apache $apr1$ MD5 mode (1600), the password was recovered:

```

hashcat '$apr1$BpZ.Q.1m$F0qqPwHSOG50URuOVQTTn.' /usr/share/wordlists/rockyou.txt -m 1600

```

• Result: `squidward`

### 📦 Borg Backup Extraction

A file named `archive.tar` was downloaded from the `/admin` page. After extraction, it was identified as a Borg Backup repository. Using the cracked password, I extracted the contents:

```

borg extract ./home/field/dev/final_archive::music_archive

```

Inside the extracted files, `note.txt` revealed Alex's SSH credentials:

• User: `alex`

• Password: `S3cretP@s3`

---

## 🚀 3. Privilege Escalation
### 🔍 Identifying the Vector

After logging in via SSH, I audited the sudo permissions for the user `alex`:

```

sudo -l

# (ALL : ALL) NOPASSWD: /etc/mp3backups/backup.sh

```

Analysis of `backup.sh` revealed that the `-c` flag allowed for arbitrary command execution due to insufficient input validation.

### 🔓 Gaining Root Shell

I exploited the Command Injection vulnerability to set the SUID bit on `/bin/bash`, allowing for an easy escalation to root:

```

sudo /etc/mp3backups/backup.sh -c 'chmod +s /bin/bash'

/bin/bash -p

```

Status: Root access obtained.

---

## 🏁 4. Conclusion & Key Takeaways
### 🔐 Security Lessons

• Information Leakage: Sensitive directories like `/etc` should never be accessible via a web server.

• Weak Credential Management: Archive passwords must be complex to resist dictionary-based cracking.

• Insecure Code Execution: Custom scripts running with `sudo` must never execute user-supplied input directly.

---

✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
