## Level 17 → 18

### Question  
There are two files in the home directory: `passwords.old` and `passwords.new`.  
The password for the next level is stored in `passwords.new` and is the only line that has been changed compared to `passwords.old`.

---

### Key Idea  
Use the `diff` command to compare both files and identify the single changed line, which contains the next level’s password.

---

### Process  

1. **Research on `diff` command**  
   - The `diff` command compares two files line by line.  
   - It highlights additions, deletions, or modifications between them.  
   - This matches the hint in the problem statement.  

2. **Compare the files**  
   Run the following command in the home directory:  
   ```bash
   diff passwords.old passwords.new
showed changed line in passwords.new file, which is flag to log-in next level.

# Reference  
https://phoenixnap.com/kb/linux-diff

# Flag
```bash
x2gLTTjFwMOhQ8oWNbMN362QKxfRqGlO
```
