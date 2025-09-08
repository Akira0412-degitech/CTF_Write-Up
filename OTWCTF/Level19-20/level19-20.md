# Level 19 - 20

## Question
To gain access to the next level, you should use the setuid binary in the home directory. Execute it without arguments to find out how to use it. The password for this level can be found in the usual place (/etc/bandit_pass), after you have used the setuid binary.  

## Process
1. Examine the setuid binary  
   Checked the permissions of the provided binary `bandit20-do` to confirm whether the setuid bit was set:
   ```bash
   ls -l bandit20-do
   ```
   Output:
   ```bash
   -rwsr-x--- 1 bandit20 bandit19 14884 Aug 15 13:16 bandit20-do
   ```
   The `s` in `-rws` confirms that the binary runs with the permissions of its owner (bandit20) when executed by members of the bandit19 group.

3. Identify usage instructions  
   Ran the binary without arguments to see how it should be used:
   ```bach
   ./bandit20-do
   ```
   Output:
   ```bash
   Run a command as another user.
     Example: ./bandit20-do id
   ```

5. Execute command as bandit20  
   Used the binary to run `cat` with bandit20’s privileges and read the password file:
   ```bash
   ./bandit20-do cat /etc/bandit_pass/bandit20
   ```

## Key Idea
The setuid permission on `bandit20-do` allows bandit19 to execute commands with the effective user ID of bandit20.  
This makes it possible to access files normally restricted to bandit20, such as the password file located in `/etc/bandit_pass/`.  

## Flag
```bash
0qXahG8ZjOVMN9Ghs7iOWsCfZyXOUbYO
```
