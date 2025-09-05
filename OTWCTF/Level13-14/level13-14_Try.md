# Bandit Level 13- 14

Q.The password for the next level is stored in /etc/bandit_pass/bandit14 and can only be read by user bandit14. For this level, you don’t get the next password, but you get a private SSH key that can be used to log into the next level. Note: localhost is a hostname that refers to the machine you are working on

## Steps
1. **Log in as bandit13**
  Use the password from the previous level:

2. **Check the home directry to see the given file named sshkey.private**

3. **Copy the key to local machine**

4. **Logout**

5. **Fix Key permissions**

`chmod 600 sshkey.private`

6. **Login using the private key**

`ssh -i sshkey.private bandit14@bandit.labs.overthewire.org -p 2220`

# Key Idea
  ssh -i allows login with a private key instead of a password
  the key file must have permissions set with chmod 600, otherwise SSH will refuse to use it
  scp (secure copy) is useful to transfer files over SSH.

# Reference 
  https://mayadevbe.me/posts/overthewire/bandit/level14/

