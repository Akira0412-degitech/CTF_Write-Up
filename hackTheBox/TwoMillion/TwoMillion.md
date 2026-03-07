# 🛡️ HTB – TwoMillion - Detailed Walkthrough
## 📌 Overview
Room Name: TwoMillion 

Platform: Hack The Box 

Difficulty: Easy 

TwoMillion is a celebratory machine marking Hack The Box reaching two million users [cite: 1]. The challenge involves bypassing invite code mechanics, exploiting API vulnerabilities for RCE, and performing a kernel-level privilege escalation on Ubuntu 22.04 [cite: 1].

---

## 🔍 1. Reconnaissance & Enumeration
Network Scanning

Initially, I used `rustscan` for fast port discovery followed by `nmap` for service identification [cite: 1].

• Open Ports:

  • `22/tcp`: OpenSSH 8.9p1 [cite: 1]

  • `80/tcp`: nginx [cite: 1]

• Domain Setup: Identified a redirect to `2million.htb` and added the entry to `/etc/hosts` [cite: 1].

Web Discovery

• Finding the Invite: Discovered an invite code entry at `/invite` [cite: 1].

• API Analysis: Inspected `/js/inviteapi.js` and found instructions to POST to `/api/v1/invite/generate` [cite: 1].

• Invite Code: Received an encoded string and decoded it via Base64 to get the valid code: `B7ELW-YGQJM-DBQQW-7FOYE` [cite: 1].

---

## 🔓 2. Initial Access & User Flag
API Exploitation & RCE

1. Broken Access Control: Found `/api/v1/admin/auth` and elevated my user to "admin" status [cite: 1].

2. Command Injection: Identified a vulnerability in the "VPN Connection Test" feature [cite: 1].

3. Reverse Shell: Used a bash payload to establish a shell as `www-data` [cite: 1].

Privilege Escalation: www-data → admin

• Credential Discovery: Found a `.env` file in the web root containing `DB_USERNAME=admin` and `DB_PASSWORD=SuperDuperPass123` [cite: 1].

• Login: Successfully switched to the admin user using `su admin` [cite: 1].

• User Flag: Recovered from `/home/admin/user.txt` [cite: 1].

  • Flag: `c6b6a68343a122c241dabb30606b422f` [cite: 1]

---

## 🚀 3. Post-Exploitation
Internal Reconnaissance

• System Mail: Found an internal mail in `/var/mail/admin` warning about a "nasty" OverlayFS / FUSE vulnerability [cite: 1].

• System Info: Confirmed the target was running Ubuntu 22.04.2 LTS with Kernel 5.15.70 [cite: 1].

---

## 🏁 4. Privilege Escalation: admin → root (Final)
Kernel Exploitation (CVE-2023-0386)

1. Weaponization: Cloned the CVE-2023-0386 exploit from GitHub [cite: 1].

2. Build on Target:

  • Transferred the source code as a `.zip` file and unzipped it on the target [cite: 1].

  • Patched `fuse.c` to include `#include <unistd.h>` to resolve compilation errors [cite: 1].

  • Successfully compiled using `make all` [cite: 1].

3. Execution:

  • Mounted the FUSE filesystem: `./fuse ./ovlcap/lower ./gc &` [cite: 1]

  • Executed the exploit: `./exp` [cite: 1]

## 4. Result: Obtained a shell with UID 0 (root) [cite: 1].

Root Flag:

• Path: `/root/root.txt` [cite: 1]

• Flag: `5f474f5f1d391d3c365131f5efecbb01` [cite: 1]

---

💡 Lessons Learned
• Configuration Security: Critical to secure `.env` files and avoid credential re-use [cite: 1].

• API Integrity: Administrative endpoints must have robust server-side validation [cite: 1].

• Patch Management: Regular kernel updates are essential to mitigate known Local Privilege Escalation (LPE) vulnerabilities [cite: 1].
