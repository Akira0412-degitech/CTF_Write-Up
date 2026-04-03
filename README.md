# 🚩 Cybersecurity CTF Write-Ups & Walkthroughs

Welcome to my personal Capture The Flag (CTF) write-ups repository! 

This repository serves as a detailed log of my journey through various cybersecurity challenges, vulnerable machines, and penetration testing labs. Each write-up documents my end-to-end methodology, from initial reconnaissance to root privilege escalation, highlighting the tools used, the vulnerabilities discovered, and the key lessons learned.

## 🎯 Purpose

* **Educational Growth:** To solidify my understanding of offensive security concepts by thoroughly documenting my attack paths.
* **Knowledge Sharing:** To provide clear, step-by-step walkthroughs that can assist other cybersecurity enthusiasts and students in their own learning journeys.
* **Professional Portfolio:** To showcase my practical skills in vulnerability assessment, exploitation, and technical reporting.

---

## 📚 Write-Up Directory

Here is a summary of the machines and challenges documented in this repository, categorized by platform:

### 🟩 Hack The Box (HTB)
| Room / Challenge | Difficulty | Category / Key Concepts |
| :--- | :---: | :--- |
| **[TwoMillion](./hackTheBox/TwoMillion/TwoMillion.md)** | Easy | API Exploitation, RCE, OverlaysFS/FUSE Kernel LPE (CVE-2023-0386) |

### 🟥 TryHackMe (THM)
| Room / Challenge | Difficulty | Category / Key Concepts |
| :--- | :---: | :--- |
| **[Agent Sudo](./TryHackMe/AgentSudo/AgentSudo.md)** | Easy | FTP Brute-force, Steganography (binwalk/steghide), Sudo Exploit (CVE-2019-14287) |
| **[Basic Pentesting](./TryHackMe/BasicPentesiting/Basic%20Pentesting.md)** | Easy | SMB Enumeration, Information Disclosure, SSH Key Cracking |
| **[Cyborg](./TryHackMe/Cyborg/cyborg.md)** | Easy | Hash Cracking, Borg Backup Repository Analysis, Command Injection |
| **[Overpass](./TryHackMe/overpass/overpass.md)** | Easy | Broken Access Control (Cookies), SSH Cracking, DNS Poisoning, Cron Job Exploit |
| **[Wonderland](./TryHackMe/Wonderland/Wonderland.md)** | Medium | Steganography, Python Library Hijacking, PATH Hijacking, Linux Capabilities |

### ☕ picoCTF
| Room / Challenge | Category | Key Concepts |
| :--- | :---: | :--- |
| **[n0s4n1ty 1](./PICOCTF/n0s4n1ty1/n0s4n1ty1.md)** | Web | Unrestricted File Upload, PHP Web Shell, Misconfigured Sudo |
| **[Irish-Name-Repo 3](./PICOCTF/Irish-Name-Repo%203/irish-name-repo3.md)** | Web | SQL Injection, Input Transformation, ROT13 Encoding |
| **[DISKO 1](./PICOCTF/DISKO1/disko1.md)** | Forensics | Raw Disk Image Analysis, FAT32 Filesystem, String Extraction |
| **[Secret of the Polyglot](./PICOCTF/Secret%20of%20the%20Polyglot/secret%20of%20the%20polyglot.md)** | Forensics | Polyglot Files (PNG+PDF), Binwalk, Zlib Extraction |

### 💻 OverTheWire (Bandit)
| Level | Category | Key Concepts |
| :--- | :---: | :--- |
| **[Level 16 → 17](./OTWCTF/Level16-17/label16-17.md)** | Network | Port Scanning, SSL/TLS Handshakes, OpenSSL `s_client` |

---

## 🛠️ Skills & Tools Demonstrated

Throughout these write-ups, various offensive security techniques and industry-standard tools are utilized:

* **Reconnaissance & Enumeration:** `Nmap`, `RustScan`, `Gobuster`, `Enum4Linux`
* **Web Exploitation:** `Burp Suite`, SQL Injection, Command Injection, Broken Access Control, Insecure File Uploads
* **Privilege Escalation (Linux):** Sudo misconfigurations, SUID binaries, PATH/Python Hijacking, Cron jobs, Linux Capabilities, Kernel Exploits (CVEs)
* **Password Cracking & Cryptography:** `Hashcat`, `John the Ripper`, `Hydra`, RSA/SSH Key Decryption
* **Digital Forensics & Steganography:** `Binwalk`, `Steghide`, `Exiftool`, `Strings`, Polyglot Analysis

---

## ⚖️ Disclaimer

**All content in this repository is strictly for educational and ethical hacking purposes.** 
The techniques demonstrated here were performed in authorized environments (CTF platforms and lab networks). Do not use these techniques against systems or networks without explicit, mutual consent from the owner. I am not responsible for any misuse of the information provided.

---

*✍️ Author: Akira Hasuo*
