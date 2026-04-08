# 🛡️ TryHackMe – Mustacchio - Writeup

## 📌 Overview
**Room Name:** Mustacchio  
**Platform:** TryHackMe  
**Difficulty:** Easy

Mustacchio is a highly educational machine that covers several core penetration testing concepts, including enumeration, database analysis, XXE (XML External Entity) attacks, SSH key cracking, and final-stage privilege escalation using PATH Injection.

---

## 🔍 1. Enumeration
### Port Scanning
I began with an `nmap` scan against the target and identified the following open ports:

```text
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.10
80/tcp   open  http    Apache httpd 2.4.18
8765/tcp open  http    nginx 1.10.3
```

- **80/tcp:** Running a standard website.
- **8765/tcp:** Running another web service (Admin portal).

### Directory Brute-forcing
Using `gobuster` to explore hidden directories, I discovered a `/custom/` directory. Inside its `js/` folder, I found a SQLite database backup file named **`users.bak`**.

---

## 📂 2. Database Analysis & Cracking
I downloaded `users.bak` and checked it with the `file` command, confirming it was a SQLite 3.x database.

```bash
sqlite3 users.bak
sqlite> .tables
sqlite> SELECT * FROM users;
```

This revealed what appeared to be administrator credentials:

- **Username:** `admin`
- **Hash:** `1868e36a6d2b17d4c2745f1659433a54d4bc5f4b`

Using `hash-identifier`, I determined the hash was SHA-1. I then used `hashcat` to crack it:

- **Cracked Password:** `bulldog19`

---

## 🌐 3. Web Exploitation (XXE)
With the cracked password, I logged into the admin panel running on port `8765`. Inside the panel, there was an `Add a comment` input form. By inspecting the source code, I found comments indicating that this form processed XML.

Realizing it was vulnerable to XXE, I crafted a payload to extract Barry's SSH private key.

**XXE Payload:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE root [
  <!ENTITY xxe SYSTEM "file:///home/barry/.ssh/id_rsa">
]>
<root>
  <name>&xxe;</name>
  <author>Barry</author>
  <comment>Checking for SSH Key</comment>
</root>
```

This payload successfully returned Barry's encrypted private SSH key (`id_rsa`).

---

## 🔓 4. Initial Access
The extracted SSH key was protected by a passphrase. To crack it, I converted the key into a crackable format using `ssh2john` and then ran John the Ripper with the `rockyou.txt` wordlist.

After successfully cracking the passphrase, I used the key to log in via SSH as `barry`. From there, I stabilized my interactive shell using Python and began internal enumeration.

At this point, I was able to read the user flag:

```bash
cat user.txt
# [REDACTED]
```
---

## 🚀 5. Privilege Escalation: barry → root
While enumerating the system, I found a very interesting binary at `/home/joe/live_log`.

- **Permissions:** The SUID bit was set, meaning it executes with `root` privileges.
- **Analysis:** Running the `strings` command on the binary revealed that it executes `tail -f /var/log/nginx/access.log` internally.

Because the binary called `tail` without specifying its absolute path (like `/usr/bin/tail`), it was vulnerable to **PATH Injection**.

**Exploitation Commands:**
```bash
# 1. Create a fake 'tail' command (which is actually bash)
echo "/bin/bash" > /tmp/tail

# 2. Make it executable
chmod +x /tmp/tail

# 3. Prepend /tmp to the PATH environment variable
export PATH=/tmp:$PATH

# 4. Execute the SUID binary
/home/joe/live_log
```

When the binary ran, it executed my fake `/tmp/tail` with root privileges instead of the real `tail` command. This instantly granted me a root shell. Finally, I read the `/root/root.txt` flag to complete the room.

```bash
cat /root/root.txt
# [REDACTED]
```

---

## 📚 Key Takeaways
- **Leftover Backup Files:** Leaving `.bak` files in web-accessible directories (like `/custom/`) can provide attackers with a critical initial foothold.
- **XML Parsing Dangers:** Allowing external entities in XML parsers directly leads to sensitive internal file disclosure via XXE attacks.
- **Relative Paths in SUID Binaries:** When calling system commands from within a SUID binary, always use the absolute path (e.g., `/usr/bin/tail`). Failing to do so makes the system highly vulnerable to PATH Injection.