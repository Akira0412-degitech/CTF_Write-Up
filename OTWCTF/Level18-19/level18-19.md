# Level 18-19

## Question
The password for the next level is stored in a file `readme` in the home directory. Unfortunately, someone has modified `.bashrc` to log you out when you log in with SSH.  

## Process
1. **Login to Level 18**  
   Normal login shows `Byebye!` and disconnects, confirming the `.bashrc` trap.

2. **Check modified file in Level 17**  
   The `.bashrc` contains:
   ```bash
   case $- in
       *i*) ;;
         *) return;;
   esac
   ```
   - Interactive → rest of the file executes (including logout).
   - Non-interactive → `.bashrc` ends early, avoiding the logout.

4. **Login in non-interactive mode**
   Use SSH with a direct command to read the `readme` file:
   ```bash
   ssh bandit18@bandit.labs.overthewire.org -p 2220 cat readme
   ```
   
## Key Idea  
The `.bashrc` file checks whether the shell is interactive.
- Interactive → continues and executes the forced logout.
- Non-interactive → stops early, avoiding the logout.

So, by logging in with SSH in non-interactive mode (running a command directly), you can bypass the logout and read the file.

## Flag
```bash
cGWpMaKXVwDUNgPAVJbWYuGHVn9zl3j8
```
