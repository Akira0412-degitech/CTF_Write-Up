# CanYouSee (Forensics)
# Quesion
How about some hide and seek?

# Process
1. **Extract zip**
   First, extract the provided file:
   ```bash
   unzip unknown.zip
   ```
2. **Identify the File Type**
   Check the extracted file:
   ```bash
   file ukn_reality.jpg
   ```
   Output:
   ```bash
   ukn_reality.jpg: JPEG image data, JFIF standard 1.01, resolution (DPI), density 72x72, segment length 16, baseline, precision 8, 4308x2875, components 3
   ```
   Confirms the file is a JPEG image.
3. **Inspect Metadata**
    Since JPEGs often contain metadata, run:
     ```bash
     exiftool ukn_reality.jpg
     ```
     Output(excerpt):
     ```bash
      Attribution URL : cGljb0NURntNRTc0RDQ3QV9ISUREM05fZGVjYTA2ZmJ9Cg==
     ```
     The suspicious string looks like Base64.

4. **Decode the Hidden String**
   Decode the Base64 value:
   ```bash
   echo "cGljb0NURntNRTc0RDQ3QV9ISUREM05fZGVjYTA2ZmJ9Cg==" | base64 -d
   ```
   Output:
   ```bash
   picoCTF{ME74D47A_HIDD3N_deca06fb}
   ```
# Key Idea
In forensics challenges, flags are often hidden in file metadata.  
Tools like exiftool reveal custom fields (e.g., "Attribution URL").  
Suspicious values such as Base64-encoded strings frequently conceal the flag.  

