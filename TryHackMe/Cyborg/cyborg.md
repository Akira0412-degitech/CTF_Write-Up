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

root.txt:
```
flag{Than5s_f0r_play1ng_H0p£_y0u_enJ053d}
```

---

## 🏁 4. Conclusion & Key Takeaways
### 🔐 Security Lessons

- Don't Leave Secret Doors Open: The biggest mistake was letting the public see the /etc folder on the website. Important files and password hashes should always be hidden away in a safe place, not left where anyone can find them.

- Pick Stronger Passwords: Using a common word like squidward is like using a physical key that everyone has a copy of. Even good encryption (like Borg Backup) can't protect you if your password is easy to guess with a dictionary attack.

- Be Careful with "Superuser" Scripts: The backup.sh script was dangerous because it trusted the user too much. If you give a script the power to run as root (the boss of the computer), it must be programmed to strictly follow rules and not just run whatever the user types in.

- Notes are for Humans, not Passwords: Writing down passwords in a note.txt file is a very common but risky habit. It only takes one small slip-up for an attacker to find that note and walk right into the system.
---

✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
