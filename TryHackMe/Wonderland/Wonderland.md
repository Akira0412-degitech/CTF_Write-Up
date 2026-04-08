# 🛡️ TryHackMe – Wonderland - Writeup

## 📌 Overview
**Room Name:** Wonderland  
**Platform:** TryHackMe  
**Difficulty:** Medium

Wonderland is a captivating room based on "Alice in Wonderland" that tests a wide range of penetration testing skills. The progression involves steganography, directory brute-forcing, and a multi-stage privilege escalation journey—moving from Alice to Rabbit, then Hatter, and finally Root—by exploiting relative path vulnerabilities and Linux Capabilities.

---

## 🔍 1. Enumeration
### Port Scanning
I started with an nmap scan to identify active services:

```text
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3
80/tcp open  http    Apache httpd 2.4.29
```

### Steganography & Initial Hints
The web service on port 80 displayed a simple image. I downloaded `whiterabbit.jpeg` and checked for embedded data. Since it was a JPEG, I used `steghide` but found it required a passphrase. I then utilized `stegseek` to crack it using the `rockyou.txt` wordlist.

```bash
stegseek -sf whiterabbit.jpeg /usr/share/wordlists/rockyou.txt
```

This extracted `hint.txt`, which contained the message: `follow the r a b b i t`.

### Directory Brute-forcing
Taking the hint literally, I used `gobuster` to look for directories. After finding `/r/`, I manually navigated through the path `/r/a/b/b/i/t/`. On the final page, the HTML source code revealed the SSH credentials for the user Alice.

- **Username:** `alice`
- **Password:** `HowDothTheLittleCrocodileImproveHisShiningTail`

---

## 🔓 2. Initial Access
Using the found credentials, I logged in via SSH:

```bash
ssh alice@<TARGET_IP>
```

---

## 🚀 3. Privilege Escalation: alice → rabbit
### The Logic: Python Library Hijacking
Running `sudo -l` showed that Alice could execute a Python script as the user `rabbit`:
```text
(rabbit) /usr/bin/python3.6 /home/alice/walrus_and_the_carpenter.py
```

**The Vulnerability:** The script performed an `import random`. In Python, the interpreter looks for modules in the current working directory before searching the standard libraries. Since the script was located in Alice’s home directory, I had the permissions to "hijack" this import.

**Exploitation:**
1.  I created a file named `random.py` in the same directory.
2.  I added a malicious payload to spawn a shell:

```python
import os
os.system("/bin/bash")
```

3.  Executing the script as `rabbit` triggered my local `random.py` instead of the system library:

```bash
sudo -u rabbit /usr/bin/python3.6 /home/alice/walrus_and_the_carpenter.py
```

**Result:** Successfully gained a shell as `rabbit`.

---

## 🚀 4. Privilege Escalation: rabbit → hatter
### The Logic: PATH Hijacking
In Rabbit's home directory, I found an SUID binary called `teaParty`. I analyzed it using `strings` and found it executed the following command:
```text
date --date='next hour' -R
```

**The Vulnerability:** The binary calls `date` using a relative path rather than an absolute path (like `/bin/date`). This means the system relies on the user's `PATH` environment variable to find the executable.

**Exploitation:**
1.  I created a fake `date` executable in `/tmp` that launches a shell.

```bash
echo "/bin/bash" > /tmp/date
chmod +x /tmp/date
```

2.  I manipulated the `PATH` variable to prioritize `/tmp`.

```bash
export PATH=/tmp:$PATH
```

3.  Running `./teaParty` forced the SUID binary to execute my malicious `/tmp/date` with elevated privileges.

**Result:** Successfully gained a shell as `hatter`. I found `password.txt` in Hatter's directory and switched to a stable SSH session.

---

## 👑 5. Final Privilege Escalation: hatter → root
### The Logic: Linux Capabilities
After exploring Hatter's account, I found no `sudo` rights or interesting SUID files. I decided to enumerate Linux Capabilities, which are often overlooked but provide granular "superpowers" to specific binaries.

**Discovery:**
```bash
getcap -r / 2>/dev/null
```
The output showed: `/usr/bin/perl = cap_setuid+ep`.

**The Vulnerability:** The `cap_setuid` capability allows the `perl` binary to manipulate its own User ID (UID). This effectively allows a user to "become" root if they can execute a script that sets the UID to 0.

**Exploitation:** Using [GTFOBins](https://gtfobins.org/gtfobins/perl/), I found as a reference, I ran a Perl one-liner to set the UID to 0 (root) and spawn a shell:

```bash
perl -e 'use POSIX qw(setuid); POSIX::setuid(0); exec "/bin/bash";'
```

**Result:** **ROOT ACCESS GRANTED.**

---

## 🚩 Flags
True to the "Alice in Wonderland" theme, the flags were placed "upside down":

- **User Flag:** Located in `/root/user.txt`
- **Root Flag:** Located in `/home/alice/root.txt`

---

## 📚 Key Takeaways
- **Relative Path Risks:** Whether it's Python imports or system commands in SUID binaries, using relative paths allows an attacker to intercept execution by placing malicious files in the search path.
- **Enumeration Depth:** When `sudo` and SUID fail, always check for Capabilities using `getcap`. It is a common "hidden" vector for privilege escalation in modern Linux rooms.
- **Contextual Clues:** The room's theme and hints (like "follow the rabbit") were essential for navigating the complex directory structure.