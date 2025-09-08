# Cookie Monster – picoCTF 2025 (Web Exploitation)

## Question
Cookie Monster has hidden his top-secret cookie recipe somewhere on his website. As an aspiring cookie detective, your mission is to uncover this delectable secret. Can you outsmart Cookie Monster and find the hidden recipe?  
Additional details will be available after launching your challenge instance.

---

## Process

1. **Initial Attempts**  
   I started by trying random usernames and passwords on the login form. However, the page responded with the message:  
   *"Me no need password. Me just need cookies!"*.  
   This hinted that the login form itself is irrelevant, and the challenge is likely focused on cookies.

2. **Inspecting Cookies**  
   Using the browser developer tools (`Application` tab → `Cookies`), I discovered a cookie named: ``` secret_recipe```
   The value looked like Base64-encoded text:
   ``` bash
   cGljb0NURntjMDBrMWVfbTBuc3Rlcl9sMHZlc19jMDBraWVzXzJDODA0MEVGfQ==
   ```
   
3. **Decoding the Cookie**  
Since the cookie value appeared to be Base64, I wrote a short Python script to decode it:

# Keyidea
# The challenge is not about login vulnerabilities,
# but about inspecting cookies.
# The hidden "secret_recipe" cookie contains the flag,
# encoded with Base64. Decode it to retrieve the flag.

# Reference
https://qiita.com/gaku-devlog/items/d1b290e6b55ec530770d

#Flag
```bash
picoCTF{c00k1e_m0nster_l0ves_c00kies_2C8040EF}
```
