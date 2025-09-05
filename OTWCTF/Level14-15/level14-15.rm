## Level 14- 15

# Question
The password for the next level can be retrieved by submitting the password of the current level to port 30000 on localhost.

# Steps
1. **Understand the task**
The password for bandit14 is sotred in `/etc/bandit_pass/bandit14`.

2. **Check the password**
To confirm there is a password, see the content in the file above.
`cat /etc/bandit_pass/bandit14`.

3. **Send the password to 30000 port in localhost**
Use `cat` to read the file and `nc` (netcat) to send it to a specific port.
`cat /etc/bandit_pass/bandit14 | nc localhost 30000`.

4. **Get the result and Login to bandit15**

## Key Idea
`cat` read the password file.
The pipe `|`sends the output of one command into another.
`nc localhost 30000` opens a TCP connection to port `30000` on the same machine.

