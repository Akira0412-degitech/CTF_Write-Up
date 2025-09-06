## Level 14- 15

# Question
The password for the next level can be retrieved by submitting the password of the current level to port 30001 on localhost using SSL/TLS encryption.

# Steps
1. ** know about openssl **
Lean basic of openssl for this level.

2. ** Find a way to connect localhost 30001 **
Connection using SSL encryption can be established using the command below:
`openssl s_client -connect localhost:30001`
3. ** Type level 15's password **

## Key Idea
- This level requires using **SSL/TLS communication** instead of plain text (like `nc`).  
- Use OpenSSL’s `s_client` to connect to `localhost:30001`.  
- After connecting, send the **current level (bandit15) password** and the server will return the next level’s password.  


## Flag
`kSkvUpMQ7lBYyCM4GBPvCvT1BfWRy0Dx`
