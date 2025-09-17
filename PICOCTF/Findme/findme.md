# PicoCTF Web Exploitation – Redirection Challenge

## Description
Help us test the form by submiting the username as test and password as test!

## What I Did
I started by exploring the challenge manually and looking at the page source. One thing that caught my attention was the following JavaScript function:

```js
function search() {
  const searchResult = document.getElementById("search-result");
  const searchTerm = document.getElementById("search-term");
  const keyword = document.getElementById("keyword");
  const comments = document.getElementById("comments");

  comments.style.visibility = "hidden";
  searchResult.style.display = "block";
  searchTerm.innerHTML = keyword.value;

  //fetching results related to the keyword value from the server
  return false;
}
```
At first glance, this looked like it might be related to fetching or displaying the flag. I analyzed it carefully:
- The function hides a comments div, but I noticed in the HTML there was no element with id comments.

- Since the code would error out on comments.style.visibility, I opened the console and manually created a fake div with that id to avoid the crash:

```bash
let fake = document.createElement("div");
fake.id = "comments";
document.body.appendChild(fake);
```
- After that, I tried calling `search()` directly in the console to see what happened.  
I noticed the function inserted user input into the search-term element without validation using `.innerHTML`.
This was clearly a possible XSS vector.  
So I started testing payloads:  
First I tried:  
```bash
<script>alert(1)</script>
```
but it did not execute because dynamically inserted <script> tags via innerHTML don’t run.  
Then I tested:  
```bash
<img src=x onerror=alert(1)>
```
Once I realized I could run arbitrary JavaScript, I attempted to fetch the flag file directly:  
```bash
fetch('/flag')
  .then(r => r.text())
  .then(d => alert(d));
```  
But this just returned `Cannot GET /flag` in my environment. That told me the flag was not accessible to me directly.  

At this point, I understood that while XSS was exploitable, the real challenge involved server redirection and hidden requests,   not simply injecting JavaScript to grab /flag.

## Where I got studk  
Even though I confirmed XSS worked, fetching /flag myself failed. I could only get error responses and couldn’t see the flag. This made me realize something else was happening behind the scenes.

## Checking the Write-up  
After consulting a community write-up, I realized that the key to the challenge wasn’t the XSS but rather the redirection chain after login.
Burp Suite revealed that after submitting the login form, there were multiple automatic redirects:

- *POST /login*

- *GET /next-page/id=cGljb0NURntwcm94aWVzX2Fs*

- *GET /next-page/id=bF90aGVfd2F5X2JlNzE2ZDhlfQ==*

These id values were Base64-encoded chunks of the flag.
## Trying It Again  

I went back and decoded the values:
- cGljb0NURntwcm94aWVzX2Fs → picoCTF{proxies_al
- bF90aGVfd2F5X2JlNzE2ZDhlfQ== → l_the_way_be716d8e}
Connected together:
```bash
picoCTF{proxies_all_the_way_be716d8e}
```

## The Best Process

If I had to redo this challenge cleanly:
1. Intercept the login with Burp Suite.
2. Carefully inspect every redirect instead of just forwarding to the end.
3. Extract the id parameters from the redirect URLs.
4. Base64 decode them to reconstruct the flag.

## Key Idea
- The login and XSS distractions were red herrings.
- The real trick was noticing the multiple redirects and realizing they carried encoded pieces of the flag.
- Burp Suite’s intercept allowed me to see what the browser would normally auto-follow and hide.
