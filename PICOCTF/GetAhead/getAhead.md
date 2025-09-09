# GET aHEAD - PicoCTF (Web Exploitation)

# Question
Find the flag being held on this server to get ahead of the competition http://mercury.picoctf.net:53554/

# Process
1. **Test the page**  
   - I started by testing the page, which allowed me to change the background color to red or blue.  

   - Inspecting the source code, I noticed that the two buttons used different HTTP methods:
   
   - Red used the GET method. Blue used the POST method.  
2. **Experiment with Burp Suite**
   - After capturing the requests in Burp Suite, I modified the method.
   
   - For example, I changed:
   ```bash
   POST /index.php HTTP/1.1
   ```
   to:
   ```bash
   GET /index.php HTTP/1.1
   ```
   - Even though the request was intended for blue, the page still changed to red.

   - This suggested that the HTTP method itself determines the behavior of the page.
3. **Try different method**
   - Since the page reacted differently to GET and POST, I experimented with other HTTP methods (```PUT```, ```HEAD```, etc.).

   - When I sent a HEAD request, the server responded with the flag inside the response headers.

# KeyIdea
   - Web applications may behave differently depending on the HTTP method used.

   - In this challenge, GET showed red and POST showed blue, meaning the method itself determined the output.

   - Trying less common methods (HEAD, OPTIONS, PUT, etc.) can sometimes reveal unexpected information.

   - Sending a HEAD request returned the flag inside the response headers.

   - In security testing and CTFs, it’s important to test all supported methods, not just GET and POST.

# Flag
```bash
picoCTF{r3j3ct_th3_du4l1ty_2e5ba39f}
```
