# 🛡️ TryHackMe – Tomghost

Full Technical Walkthrough & Root Compromise Report

## 📌 Overview

Room Name: Tomghost

Platform: TryHackMe

Difficulty: Easy

Category: Apache Tomcat / AJP Protocol / PGP Cracking / Misconfigured Sudo

This machine walks through a multi-stage exploitation path starting from an exposed AJP port, leveraging the Ghostcat vulnerability (CVE-2020-1938) to gain initial access, followed by offline PGP cracking for lateral movement, and finally escalating privileges through a misconfigured zip binary in the sudoers file.

## 🔍 1. Enumeration Phase

To begin, I ran a full port scan using Rustscan to map out the services running on the target system.

```bash
rustscan -a <target_ip> -- -sV
```

The scan revealed SSH on port 22, an Apache Tomcat web service on port 8080, and more importantly, an uncommon open port: 8009, which was identified as the Apache JServ Protocol (AJP).

Given the relationship between AJP and Tomcat, and knowing that AJP is not typically exposed externally, I suspected a possible misconfiguration. This prompted a vulnerability check using searchsploit:

```bash
searchsploit tomcat ajp
```

This search returned the Ghostcat vulnerability (CVE-2020-1938), which allows attackers to read arbitrary files from the Tomcat server via the AJP service.

## 🔓 2. Initial Access

I then used a public Ghostcat exploit to attempt reading sensitive files from the server. The original exploit was written in Python 2, so I modified it slightly for Python 3 (e.g., adding .decode('utf-8') where needed):

```bash
python3 48143.py <target_ip>
```

This script successfully retrieved the contents of the WEB-INF/web.xml file, from which I extracted hardcoded credentials:

• Username: skyfuck  
• Password: 8730281lkjlkjdqlksalks

I used these credentials to log in via SSH:

```bash
ssh skyfuck@<target_ip>
```

A shell was obtained with this user.

## 🚀 3. Privilege Escalation Discovery

After gaining a foothold, I checked the user's sudo permissions:

```bash
sudo -l
```

This returned nothing of interest—skyfuck had no sudo privileges. I began manually inspecting the user’s home directory and discovered two files:

• `tryhackme.asc` – a GPG private key  
• `credential.pgp` – an encrypted file

It seemed likely that the private key could be used to decrypt credential.pgp, so I copied the key to my local machine and prepared to crack it offline.

Using gpg2john to extract the key's hash, and john with the rockyou wordlist, I attempted to recover the passphrase:

```bash
gpg2john tryhackme.asc > hash
john --wordlist=/usr/share/wordlists/rockyou.txt hash
```

The passphrase was cracked successfully as: alexandru

I imported the key and decrypted the PGP file:

```bash
gpg --import tryhackme.asc
gpg --decrypt credential.pgp
```

The decrypted content revealed another set of credentials:

• Username: merlin  
• Password: asuyusdoiuqoilkda312j31k2j123j1g23g12k3g12kj3gk12jg3k12j3kj123j

I switched users with:

```bash
su merlin
```

At this point, I captured the user flag.  
user.txt: `THM{GhostCat_1s_so_cr4sy}`

## 🛠️ 4. Exploitation (Root Privilege Escalation)

As the user merlin, I once again checked for sudo permissions:

```bash
sudo -l
```

This time, the output showed:

```text
(root : root) NOPASSWD: /usr/bin/zip
```

According to GTFOBins, the zip utility can be abused to execute arbitrary commands when using the -T (test) and -TT options. Since it could be run with root privileges, this presented a direct path to privilege escalation.

I executed the following command to spawn a root shell:

```bash
sudo zip /tmp/pwn.zip /etc/hosts -T -TT '/bin/sh #'
```

Then confirmed my privilege level:

```bash
whoami

root

```

I accessed /root/root.txt to retrieve the root flag.
root.txt: `THM{Z1P_1S_FAKE}`

## 🧠 Key Takeaways

Unusual Ports Lead to Unusual Vulnerabilities
Discovering AJP on port 8009 was the initial pivot point. Investigating this rarely-used port led to Ghostcat, which ultimately enabled the entire attack chain.

Offline Cracking Is a Silent But Powerful Technique
Exporting and cracking the GPG key locally avoided triggering alarms and allowed lateral movement with minimal noise.

Misconfigured Sudo Permissions Are Dangerous
Allowing sudo access to tools like zip—even if seemingly benign—can lead to full system compromise. Every binary in sudo should be vetted for potential abuse via GTFOBins or equivalent.

✍️ Author: Akira Hasuo
