# 🕵️ tomghost: Penetration Testing Report

## 1. Enumeration Phase: Identifying the Entry Point
The assessment began with a full port scan to map the target's attack surface.

* **Scanning with Rustscan**:
  By running `$ rustscan -a <Target_IP> -- -sV`, I identified standard ports like 22 (SSH) and 8080 (HTTP), but the presence of port **8009 (AJP)** was the key outlier.
* **Vulnerability Research**:
  Seeing an unusual port like AJP led me to search for known exploits using `searchsploit`:
  `$ searchsploit tomcat ajp`
  This confirmed the server was likely vulnerable to **Ghostcat (CVE-2020-1938)**, a file inclusion vulnerability.

---

## 2. Initial Access: Exploiting Ghostcat
With a specific vulnerability in mind, I moved to exploit the AJP service to extract sensitive configuration files.

* **Execution & Debugging**:
  The exploit script required manual modification to run in a Python 3 environment. I patched the communication logic with `.decode('utf-8')` to handle the data stream correctly.
  `$ python3 48143.py <Target_IP>`
* **Credential Recovery**:
  The exploit successfully read the internal `web.xml` file, which leaked cleartext credentials:
  - User: **skyfuck**
  - Pass: **8730281lkjlkjdqlksalks**
* **Access**:
  I established the first foothold by logging in via SSH:
  `$ ssh skyfuck@<Target_IP>`

---

## 3. Privilege Escalation Discovery: Lateral Movement
Once inside, I needed to escalate my privileges, but the initial user `skyfuck` was heavily restricted.

* **Local Enumeration**:
  A check with `$ sudo -l` revealed that `skyfuck` had no sudo permissions. However, a manual search of the home directory uncovered two critical PGP files: `tryhackme.asc` (Private Key) and `credential.pgp` (Encrypted Data).
* **Cracking the PGP Passphrase**:
  Since the private key was password-protected, I moved the file to my local machine for offline cracking:
  1. Extract hash: `$ gpg2john tryhackme.asc > hash`
  2. Brute-force: `$ john --wordlist=/usr/share/wordlists/rockyou.txt hash`
  The password was identified as **"alexandru"**.
* **Decryption & User Pivot**:
  Using the cracked passphrase, I decrypted the data to reveal the credentials for the next user, **merlin**:
  - Pass: **asuyusdoiuqoilkda312j31k2j123j1g23g12k3g12kj3gk12jg3k12j3kj123j**
  I then switched users via `$ su merlin` and captured the User Flag.

---

## 4. Exploitation: Final Ascent to Root
Operating as `merlin`, I performed a final check for system misconfigurations.

* **Binary Misconfiguration**:
  Running `$ sudo -l` again revealed a high-risk entry:
  `(root : root) NOPASSWD: /usr/bin/zip`
* **Root Shell via GTFOBins**:
  The `zip` command can execute arbitrary programs during its "test" phase. I leveraged this to spawn a root shell:
  `$ sudo zip /tmp/pwn.zip /etc/hosts -T -TT '/bin/sh #'`
* **Completion**:
  The command granted a shell with effective UID 0. I confirmed my identity with `whoami` and retrieved the final flag from `/root/root.txt`.

---

## 💡 Key Takeaways
1. **Unusual Ports Matter**: The discovery of port 8009 (AJP) was the catalyst for the entire breach. Standard ports often lead to dead ends; outliers lead to exploits.
2. **Offline Cracking is Powerful**: Protecting a secret with PGP is only as secure as the passphrase. Using `john` allowed for a silent, high-speed attack without alerting the server.
3. **Sudoers Misconfiguration**: Granting sudo rights to a binary like `zip` is dangerous because many utilities have "escape" features that can spawn shells. Always follow the principle of least privilege (PoLP).
