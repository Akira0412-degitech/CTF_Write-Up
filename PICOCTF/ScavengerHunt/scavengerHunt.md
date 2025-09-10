# Scavenger Hunt – PicoCTF (Web Exploitation)

## Question
The challenge provides the following prompt:  
There is some interesting information hidden around this site: http://mercury.picoctf.net:39698/. Can you find it?

---

## Process

1. **Initial Exploration**  
   I began by interacting with the visible elements on the homepage (`How` and `What` buttons).  
   These actions did not reveal any useful information related to the flag.

2. **Inspecting Source Files**  
   Examining the `index.html` file revealed the **first fragment** of the flag:  
   - From HTML:
    ```bash
   <!-- Here's the first part of the flag: picoCTF{t -->
    ```
    Additional fragments were discovered in linked resources:  
    - From ```mycss.css```:
    ```bash
    /* CSS makes the page look nice, and yes, it also has part of the flag. Here's part 2: h4ts_4_l0 */
    ```  
    - From ```myjs.js```:  
    ```bash
    /* How can I keep Google from indexing my website? */
    ```
3. **Follow the hint**  
   The JavaScript comment hinted at search engine indexing, suggesting a look at ```robots.txt```.
   Run:
   ```bash
    curl http://mercury.picoctf.net:39698/robots.txt
   ```
   the output:
   ```bash
   User-agent: *
    Disallow: /index.html
    Part 3: t_0f_pl4c
    I think this is an apache server... can you Access the next flag?
    ```
   
4. **Explore Apache-related files**  
  The Apache reference suggested checking .htaccess.
   Accessing it revealed: 
   ```bash
   Part 4: 3s_2_lO0k
    I love making websites on my Mac, I can Store a lot of information there.
    ```
5. **Use the Mac hint**  
   The mention of “Mac” pointed to .DS_Store, a common hidden file on macOS systems.
   Run:
   ```bash
   curl http://mercury.picoctf.net:39698/.DS_Store
    ```
   the output showing the final part:
   ```bash
   Congrats! You completed the scavenger hunt. Part 5: _fa04427c}
    ```
# Key Idea
  - Hidden flag fragments were distributed across multiple files: index.html, mycss.css, robots.txt, .htaccess, and .DS_Store.

  - Each hint pointed logically to the next location, reinforcing the importance of following contextual clues.

# Flag
```bash
picoCTF{th4ts_4_l0t_0f_pl4c3s_2_lO0k_fa04427c}
```
   
   
   
   
