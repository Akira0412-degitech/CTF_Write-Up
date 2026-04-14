# 🚩 CTF Write-Ups & Penetration Testing Walkthroughs

> A structured collection of end-to-end write-ups from CTF platforms and penetration testing labs — documenting methodology, tooling, vulnerabilities, and lessons learned.

---

## 👤 About

**Author:** Akira Hasuo  
**Focus:** Offensive security, web exploitation, Linux privilege escalation  
**Platforms:** Hack The Box · TryHackMe · picoCTF · OverTheWire

Each write-up follows a consistent structure: reconnaissance → exploitation → privilege escalation → key takeaways. The goal is to serve as both a learning log and a technical portfolio.

---

## 📂 Index

### 🟥 TryHackMe

| Room | Difficulty | Category | Key Techniques |
|------|-----------|----------|----------------|
| [Agent Sudo](TryHackMe/AgentSudo/AgentSudo.md) | Easy | Steganography / CVE | User-Agent manipulation, steghide, CVE-2019-14287 |
| [BricksHeist](TryHackMe/BricksHeist/BricksHeist.md) | Easy | WordPress / RCE / Forensics | CVE-2024-25600 (Bricks Builder RCE), masquerading services, triple-encoded wallet decode, LockBit attribution |
| [Basic Pentesting](TryHackMe/BasicPentesiting/Basic%20Pentesting.md) | Easy | Enumeration / Auth | SMB enumeration, hydra, ssh2john |
| [Chill Hack](TryHackMe/Chillhack/Chillhack.md) | Easy | Web / PrivEsc | Command injection (Base64 bypass), SQLi, Docker group |
| [Chocolate Factory](TryHackMe/ChocolateFactory/ChocolateFactory.md) | Easy | Steganography / PrivEsc | steghide, hashcat, vi sudo escape, Fernet decryption |
| [Cyborg](TryHackMe/Cyborg/cyborg.md) | Easy | Backup / PrivEsc | Borg Backup extraction, command injection in backup script |
| [Lookup](TryHackMe/lookup/Lookup.md) | Easy | Web / PrivEsc | User enumeration, elFinder RCE (CVE-2021-32682), PATH hijacking, sudo look |
| [Mustacchio](TryHackMe/Mustacchio/Mustacchio.md) | Easy | Web / PrivEsc | SQLite analysis, XXE attack, ssh2john, PATH injection |
| [Overpass](TryHackMe/overpass/overpass.md) | Easy | Web / PrivEsc | Cookie manipulation, SSH key cracking, DNS poisoning, cron exploitation |
| [Teams](TryHackMe/Teams/Teams.md) | Easy | Web / LFI / PrivEsc | vhost enumeration, LFI, SSH key in sshd_config, writable cron script |
| [Tomghost](TryHackMe/tomghost/tomghost.md) | Easy | CVE / PrivEsc | Ghostcat (CVE-2020-1938), GPG key cracking, zip GTFOBins |
| [Wgel CTF](TryHackMe/Wgel/Wgel.md) | Easy | Web / PrivEsc | SSH key discovery, sudo wget → /etc/passwd overwrite |
| [Wonderland](TryHackMe/Wonderland/Wonderland.md) | Medium | Steganography / PrivEsc | stegseek, Python library hijacking, Linux Capabilities (perl) |

---

### 🟩 Hack The Box

| Machine | Difficulty | Category | Key Techniques |
|---------|-----------|----------|----------------|
| [TwoMillion](hackTheBox/TwoMillion/TwoMillion.md) | Easy | Web / CVE | API abuse, Broken Access Control, command injection, CVE-2023-0386 (OverlayFS) |

---

### ☕ picoCTF

| Challenge | Category | Key Techniques |
|-----------|----------|----------------|
| [Can You See](PICOCTF/CanYouSee/unknown/unknown.md) | Forensics | exiftool metadata extraction, Base64 decode |
| [Cookie Monster](PICOCTF/CookieMonster/CookieMonster.md) | Web | Browser cookie analysis, Base64 decode |
| [Cookies](PICOCTF/Cookies/Cookies.md) | Web | Cookie value iteration |
| [DISKO1](PICOCTF/DISKO1/disko1.md) | Forensics | gzip decompress, FAT32 analysis, strings |
| [Findme](PICOCTF/Findme/findme.md) | Web | Burp Suite redirect tracking, Base64 flag reconstruction |
| [GET aHEAD](PICOCTF/GetAhead/getAhead.md) | Web | HTTP method manipulation (HEAD request) |
| [Irish Name Repo 3](PICOCTF/Irish-Name-Repo%203/irish-name-repo3.md) | Web | SQL injection |
| [Login](PICOCTF/Login/login.md) | Web | JavaScript source analysis, hardcoded Base64 credentials |
| [n0s4n1ty 1](PICOCTF/n0s4n1ty1/n0s4n1ty1.md) | Web | PHP file upload → RCE, sudo NOPASSWD |
| [Scavenger Hunt](PICOCTF/ScavengerHunt/scavengerHunt.md) | Web | robots.txt, .htaccess, .DS_Store enumeration |
| [Secret of the Polyglot](PICOCTF/Secret%20of%20the%20Polyglot/secret%20of%20the%20polyglot.md) | Forensics | binwalk, polyglot file (PNG+PDF) analysis |

---

### 💻 OverTheWire — Bandit

| Level | Key Techniques |
|-------|----------------|
| [Level 13 → 14](OTWCTF/Level13-14/level13-14_Try.md) | SSH private key auth, scp, chmod 600 |
| [Level 14 → 15](OTWCTF/Level14-15/level14-15.md) | Netcat, local port communication |
| [Level 15 → 16](OTWCTF/Level15-16/level15-16.md) | OpenSSL s_client, SSL/TLS |
| [Level 16 → 17](OTWCTF/Level16-17/label16-17.md) | Nmap service scan, SSL server identification, `-quiet` flag |
| [Level 17 → 18](OTWCTF/Level17-18/level17-18.md) | diff, file comparison |
| [Level 18 → 19](OTWCTF/Level18-19/level18-19.md) | Non-interactive SSH, .bashrc bypass |
| [Level 19 → 20](OTWCTF/Level19-20/level19-20.md) | SetUID binary exploitation |

---

## 🛠️ Skills & Tools

| Category | Tools & Techniques |
|----------|--------------------|
| **Reconnaissance** | `rustscan`, `nmap`, `gobuster`, `ffuf`, `enum4linux` |
| **Web Exploitation** | `Burp Suite`, LFI, SQLi, XXE, Command Injection, File Upload, Broken Access Control |
| **Password Cracking** | `hashcat`, `john`, `hydra`, `ssh2john`, `gpg2john` |
| **Privilege Escalation** | Sudo misconfigs, SUID binaries, PATH hijacking, Cron jobs, Docker group, Linux Capabilities, Kernel CVEs |
| **Steganography & Forensics** | `steghide`, `stegseek`, `binwalk`, `exiftool`, `strings` |
| **Exploitation Frameworks** | `msfconsole`, `searchsploit` |
| **Cryptography** | `openssl`, `gpg`, Base64, Fernet |

---

## ⚖️ Disclaimer

All techniques documented in this repository were performed exclusively within authorized environments (CTF platforms and dedicated lab networks). This content is intended solely for educational and ethical hacking purposes. Do not apply these techniques against any system or network without explicit written authorization from the owner.

---

*✍️ Author: Akira Hasuo — Created for educational and portfolio purposes only*
