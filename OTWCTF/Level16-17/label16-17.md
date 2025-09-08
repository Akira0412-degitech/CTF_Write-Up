# Level 16 → 17

## Question
The credentials for the next level can be retrieved by submitting the password of the current level to a port on localhost in the range 31000–32000. First find out which of these ports have a server listening on them. Then find out which of those speak SSL/TLS and which don’t. There is only 1 server that will give the next credentials; the others will simply send back whatever you send to them.

## My Process
1. **Port scanning with nc**  
   Based on the hint, I first learned how to use the `nc` command and scanned the given range of ports:  
   ```bash
   nc -z localhost 31000-32000
   ```
   This showed 5 active listening ports.

2. **Testing each port**  
   I tried connecting to each of the discovered ports and submitting the Bandit16 password. Two ports accepted SSL connections, but instead of giving the key, they responded with `KEYUPDATE`.

3. **Investigating the KEYUPDATE issue**  
   In the challenge description, I noticed a note:  
   > Helpful note: Getting “DONE”, “RENEGOTIATING” or “KEYUPDATE”? Read the “CONNECTED COMMANDS” section in the manpage.  

4. **Checking the OpenSSL manpage**  
   I ran:
   ```bash
   man openssl-s_client
   ```
   and learned that if input starts with `k` or `K`, OpenSSL interprets it as a special command (`KEYUPDATE`), instead of sending the text to the server.

5. **Fixing with the -quiet option**  
   To prevent this, I used the `-quiet` option so my password would be sent as data, not as a command. This worked and the server returned the RSA private key for Bandit17:  
   ```bash
   echo "kSkvUpMQ7lBYyCM4GBPvCvT1BfWRy0Dx" | openssl s_client -connect localhost:31790 -quiet
   ```

6. **Copying the key locally**  
   I copied everything between `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----` into a local file:  
   ```bash
   nano bandit17.key
   ```
   and then restricted its permissions:  
   ```bash
   chmod 600 bandit17.key
   ```

7. **Using the key to log in**  
   Finally, I used the RSA private key with SSH to log in as Bandit17:  
   ```bash
   ssh -i bandit17.key bandit17@bandit.labs.overthewire.org -p 2220
   ```

## Best Solution
1. Scan the ports:  
   ```bash
   nmap -p31000-32000 -sV localhost
   ```
   → Identify the port that supports SSL/TLS.

2. Send the Bandit16 password to the SSL port:  
   ```bash
   echo "kSkvUpMQ7lBYyCM4GBPvCvT1BfWRy0Dx" | openssl s_client -connect localhost:31790 -quiet
   ```

3. Copy the returned RSA private key into a local file (e.g., `bandit17.key`), set permissions:  
   ```bash
   chmod 600 bandit17.key
   ```

4. Log in as Bandit17:  
   ```bash
   ssh -i bandit17.key bandit17@bandit.labs.overthewire.org -p 2220
   ```

## Key Idea
- Only one port in the 31000–32000 range supports SSL/TLS.  
- When using `openssl s_client`, the `-quiet` option prevents OpenSSL from interpreting password input as commands (like `KEYUPDATE`).  
- The server returns an RSA private key instead of a plain password; this key must be saved locally and used with SSH to log in as Bandit17.

# Flag
```bash
-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAvmOkuifmMg6HL2YPIOjon6iWfbp7c3jx34YkYWqUH57SUdyJ
imZzeyGC0gtZPGujUSxiJSWI/oTqexh+cAMTSMlOJf7+BrJObArnxd9Y7YT2bRPQ
Ja6Lzb558YW3FZl87ORiO+rW4LCDCNd2lUvLE/GL2GWyuKN0K5iCd5TbtJzEkQTu
DSt2mcNn4rhAL+JFr56o4T6z8WWAW18BR6yGrMq7Q/kALHYW3OekePQAzL0VUYbW
JGTi65CxbCnzc/w4+mqQyvmzpWtMAzJTzAzQxNbkR2MBGySxDLrjg0LWN6sK7wNX
x0YVztz/zbIkPjfkU1jHS+9EbVNj+D1XFOJuaQIDAQABAoIBABagpxpM1aoLWfvD
KHcj10nqcoBc4oE11aFYQwik7xfW+24pRNuDE6SFthOar69jp5RlLwD1NhPx3iBl
J9nOM8OJ0VToum43UOS8YxF8WwhXriYGnc1sskbwpXOUDc9uX4+UESzH22P29ovd
d8WErY0gPxun8pbJLmxkAtWNhpMvfe0050vk9TL5wqbu9AlbssgTcCXkMQnPw9nC
YNN6DDP2lbcBrvgT9YCNL6C+ZKufD52yOQ9qOkwFTEQpjtF4uNtJom+asvlpmS8A
vLY9r60wYSvmZhNqBUrj7lyCtXMIu1kkd4w7F77k+DjHoAXyxcUp1DGL51sOmama
+TOWWgECgYEA8JtPxP0GRJ+IQkX262jM3dEIkza8ky5moIwUqYdsx0NxHgRRhORT
8c8hAuRBb2G82so8vUHk/fur85OEfc9TncnCY2crpoqsghifKLxrLgtT+qDpfZnx
SatLdt8GfQ85yA7hnWWJ2MxF3NaeSDm75Lsm+tBbAiyc9P2jGRNtMSkCgYEAypHd
HCctNi/FwjulhttFx/rHYKhLidZDFYeiE/v45bN4yFm8x7R/b0iE7KaszX+Exdvt
SghaTdcG0Knyw1bpJVyusavPzpaJMjdJ6tcFhVAbAjm7enCIvGCSx+X3l5SiWg0A
R57hJglezIiVjv3aGwHwvlZvtszK6zV6oXFAu0ECgYAbjo46T4hyP5tJi93V5HDi
Ttiek7xRVxUl+iU7rWkGAXFpMLFteQEsRr7PJ/lemmEY5eTDAFMLy9FL2m9oQWCg
R8VdwSk8r9FGLS+9aKcV5PI/WEKlwgXinB3OhYimtiG2Cg5JCqIZFHxD6MjEGOiu
L8ktHMPvodBwNsSBULpG0QKBgBAplTfC1HOnWiMGOU3KPwYWt0O6CdTkmJOmL8Ni
blh9elyZ9FsGxsgtRBXRsqXuz7wtsQAgLHxbdLq/ZJQ7YfzOKU4ZxEnabvXnvWkU
YOdjHdSOoKvDQNWu6ucyLRAWFuISeXw9a/9p7ftpxm0TSgyvmfLF2MIAEwyzRqaM
77pBAoGAMmjmIJdjp+Ez8duyn3ieo36yrttF5NSsJLAbxFpdlc1gvtGCWW+9Cq0b
dxviW8+TFVEBl1O4f7HVm6EpTscdDxU+bCXWkfjuRb7Dy9GOtt9JPsX8MBTakzh3
vBgsyi/sN3RqRBcGU40fOoZyfAMT8s1m/uYv52O6IgeuZ/ujbjY=
-----END RSA PRIVATE KEY-----
```

# Reference 
https://ja.linux-console.net/?p=19689
