# Cookies – picoCTF (Web Exploitation)

## Question
Who doesn't love cookies? Try to figure out the best one.  
http://mercury.picoctf.net:6418/

---

## Process

1. **Initial Attempts**  
   - I began by entering random cookie names such as `chocolate` and `vanilla` into the input field.  
   - Each attempt resulted in the error message:  
     ```
     That doesn't appear to be a valid cookie.
     ```
   - This suggested that the challenge is not based on form input, but rather on HTTP cookies.

2. **Inspecting Cookies**  
   - Using the browser’s developer tools, I observed that a cookie named `name` was being set.  
   - When invalid input was submitted, its value was `-1`, corresponding to the error message above.  

3. **Testing Cookie Values**  
   - I modified the cookie value directly and reloaded the page.  
   - Results of some values:
     ```
     value = -1 → That doesn't appear to be a valid cookie.
     value = 0  → I love snickerdoodle cookies!
     value = 1  → I love chocolate chip cookies!
     value = 2  → I love oatmeal raisin cookies!
     value = 3  → I love gingersnap cookies!
     ```
   - This confirmed that the challenge logic depends on the numeric cookie value.

4. **Brute-forcing Cookie Values**  
   - Since the values appeared to correspond to different cookie types, I iterated through the range manually.  
   - By the time I reached value `29`, I had covered all options.  
   - At value `18`, the page finally revealed the hidden flag.  

---

## Key Idea

The form input is irrelevant — the real mechanism is the "name" cookie.  
Changing the cookie's value cycles through different responses.  


#Flag
```bash
picoCTF{3v3ry1_l0v3s_c00k135_88acab36}
```
