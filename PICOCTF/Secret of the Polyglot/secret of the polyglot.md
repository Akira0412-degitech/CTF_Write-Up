## PicoCTF - Secret of the Polyglot (Foreniscs)

# Description   
The Network Operations Center (NOC) of your local institution picked up a suspicious file, they're getting conflicting information on what type of file it is. They've brought you in as an external expert to examine the file. Can you extract all the information from this strange file?
Download the suspicious file here.

# Provided files
  ` flag2of2-final.pdf`

# Step-by-Step Solution
1. Check file type
   The file is labeled as .pdf, but running file shows:
   ```bash
   file flag2of2-final.pdf
   ```
   the output:
   ```
   flag2of2-final.png: PNG image data, 50 x 50, 8-bit/color RGBA, non-interlaced
   ```
   The file is actually a PNG image, not a PDF.

2. Renaming and initial inspection
   After renaming to .png, opening it revealed the first part of the flag directly inside the image:
   ```bash
   picoCTF{f1u3n7_
   ```
   Since this is incomplete, further investigation was needed.

4. Metadata and strings
   Since It is png file, there are few things to hide flag. I tried:
   ```bash
   exiftool flag2of2-final.png
   ```
   ```bash
   strings flag2of2-final.png
   ```
   No useful flag-related information appeared here.

5. Searching for embedded files
   Next, I used binwalk to look for hidden content inside the PNG:
   ```bash
   binwalk flag2of2-final.png
   ```
   output:
   ```bash
    DECIMAL       HEXADECIMAL     DESCRIPTION
    --------------------------------------------------------------------------------
    0             0x0             PNG image, 50 x 50, 8-bit/color RGBA, non-interlaced
    914           0x392           PDF document, version: "1.4"
    1149          0x47D           Zlib compressed data, default compression
   ```
 The PNG hides a PDF and zlib-compressed data.
   ```bash
   binwalk -e flag2of2-final.png
   ```
   This created a directory `_flag2of2-final.png.extracted`.
   
6. Exploring extracted files
   Inside the extraction folder:
   ```bash
   ls
   47D  47D.zlib  out.txt
   ```
   - `47D` -> ASCII text
   - `47D.zlib` -> zlib-compressed file
   - `out.txt` -> empty
   Checking the ASCII file:
  ```bash
    cat 47D
  ```
  Output:
  ```bash
    q 0.1 0 0 0.1 0 0 cm
    0 g
    q
    10 0 0 10 0 0 cm BT
    /R7 16 Tf
    1 0 0 1 50 250 Tm
    (1n_pn9_&_pdf_7f9bccd1})Tj
    ET
    Q
    Q
  ```
  The key string `(1n_pn9_&_pdf_7f9bccd1})` clearly resembles the second part of the flag.
# Flag 
  ```bash
  picoCTF{f1u3n7_1n_pn9_&_pdf_7f9bccd1}
  ```

# Key Idea
- Polyglot files: A file can masquerade as multiple formats (PDF + PNG in this case). Always verify with `file`
- binwalk is your friend: PNGs often hide additional files inside; `binwalk -e` quickly extracts them.
- Zlib & ASCII extraction: Flags may be split across compressed data or embedded text. Don’t stop after the first partial discovery.
   
   
   
