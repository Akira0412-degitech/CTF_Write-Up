CTF Write-up: Cyborg (TryHackMe)
1. Introduction
Hi there! Today we're looking at Cyborg, a beginner-friendly room on TryHackMe. This box is great for learning how to move from web enumeration to cracking encrypted backups and eventually exploiting a script to get root access.

2. Scouting the Target (Reconnaissance)
Every hack starts with looking around. I used a tool called `rustscan` to see which "doors" (ports) were open on the machine.

The Scan:

```

rustscan -a <IP_ADDRESS>

```

Results:

• Port 22 (SSH): For remote login.

• Port 80 (HTTP): A web server is running.

Since there's a web server, I checked it out in my browser. It looked like a standard Apache page, so I used `gobuster` to find hidden folders.

Hidden Folders Found:

• `/admin`: I found a "Shoutbox" where a user named Alex was chatting about an insecure proxy.

• `/etc`: This is a goldmine! I found a `passwd` file with a scrambled password (hash) and a `squid.conf` file.

3. Breaking In (Exploitation)
Cracking the Hash

The password hash looked like this: `music_archive:$apr1$BpZ.Q.1m$...` Using a tool called `hashcat` and a list of common passwords (`rockyou.txt`), I was able to "un-scramble" it.

• Cracked Password: `squidward`

Exploring the Backup

I found a file called `archive.tar` in the admin area. After downloading it, I realized it was a Borg Backup. Borg is a tool that encrypts and compresses files. I used the password I just cracked to look inside:

```

borg extract ./path/to/archive::music_archive

```

Inside the backup, I found a note in Alex's documents:

• User: `alex`

• Password: `S3cretP@s3`

Getting the First Flag

With these credentials, I logged in via SSH:

```

ssh alex@<IP_ADDRESS>

```

I found the first flag in `user.txt`! User Flag: `flag{1_hop3_y0u_ke3p_th3_arch1v3s_saf3}`

4. Becoming "Root" (Privilege Escalation)
In Linux, the "root" user has total control. I checked what special powers Alex had using `sudo -l`. It turns out Alex can run a script called `backup.sh` as root without a password.

The Flaw: I looked at the code of `backup.sh` and noticed it was poorly written. It takes a command from the user and runs it directly. This is called Command Injection.

The Trick: I told the script to change the permissions of the system terminal (`/bin/bash`) so that I could run it as a superuser:

```

sudo /etc/mp3backups/backup.sh -c 'chmod +s /bin/bash'

```

Then I simply ran:

```

/bin/bash -p

```

Now I am the root user! I headed to the `/root` folder to get the final flag. Root Flag: `flag{Than5s_f0r_play1ng_H0p£_y0u_enJ053d}`

5. Lessons Learned
• Don't leave backups public: Anyone can download them and try to crack them.

• Weak passwords are dangerous: "Squidward" is easy to crack. Use complex ones!

• Secure your scripts: If a script runs as root, it must be very careful about how it handles user input.

Happy Hacking!
