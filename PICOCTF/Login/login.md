# Login

## Description
My dog-sitter's brother made this website but I can't get in; can you help?

---

## Process I Did
When I inspected the website, I looked at the source files and found `index.js`. This file contained the login validation logic written entirely in JavaScript:

```js
document.querySelector("form").addEventListener("submit", (e => {
  e.preventDefault();
  const r = { u: "input[name=username]", p: "input[name=password]" }, t = {};
  for (const e in r)
    t[e] = btoa(document.querySelector(r[e]).value).replace(/=/g, "");
  return "YWRtaW4" !== t.u 
    ? alert("Incorrect Username") 
    : "cGljb0NURns1M3J2M3JfNTNydjNyXzUzcnYzcl81M3J2M3JfNTNydjNyfQ" !== t.p 
    ? alert("Incorrect Password") 
    : void alert(`Correct Password! Your flag is ${atob(t.p)}.`)
}))
```
Here’s what happens step by step:

- r.u selects the input field for username, and r.p selects the field for password.

- A loop encodes the values from these fields with btoa (Base64 encoding) and removes any = padding.

- The script then compares the encoded results against two hardcoded Base64 strings:

- `YWRtaW4` → this decodes to `admin` (the correct username).

- `cGljb0NURns1M3J2M3JfNTNydjNyXzUzcnYzcl81M3J2M3JfNTNydjNyfQ` → decoding this gives the correct password, which is also the flag. `picoCTF{53rv3r_53rv3r_53rv3r_53rv3r_53rv3r}`

- So the credentials are:

Username: `admin`

Password: `picoCTF{53rv3r_53rv3r_53rv3r_53rv3r_53rv3r}`

Entering these reveals the flag.

## Key Idea

The login validation was handled completely on the client-side. By checking the JavaScript source, the hardcoded Base64 values for username and password were exposed. Decoding them directly revealed the required credentials and the flag.
