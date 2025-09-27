# PicoCTF DISKO 1 (Forenics)

## Description
Can you find the flag in this disk image?
Download the disk image here.

## Provided 
`disko-1.dd.gz`

## Process
1. File Identification
   I run `file` command to confirm file type.
   
   ```
   file disko-1.dd.gz
   ```
   output:

   ```
   disko-1.dd.gz: gzip compressed data, was "disko-1.dd", last modified: Thu May 15 18:48:20 2025, from Unix, original size modulo 2^32 52428800
   ```
   Output shows it was a gzip-compressed file.
   So I extracted it:
   ```
   gzip -d disko-1.dd.gz
   ```
   
2. Identification of extracted file
   After extraction, I identified the raw image:
   
   ```
   file disko-1.dd
   ```
   output:

   ```
   disko-1.dd: DOS/MBR boot sector, code offset 0x58+2, OEM-ID "mkfs.fat", Media descriptor 0xf8, sectors/track 32, heads 8, sectors 102400 (volumes > 32 MB), FAT (32 bit), sectors/FAT 788, serial number 0x241a4420, unlabeled
   ```
   Output confirmed it was a FAT32 disk image of about 50 MB.

3. Content check
   Since mounting tools were not available, I searched for readable strings:

   ```
   strings disko-1.dd | grep pico
   ```
   This revealed the flag:

   ```
   ...
   ...
   picoCTF{1t5_ju5t_4_5tr1n9_be6031da}
   ```
## Flag

```
picoCTF{1t5_ju5t_4_5tr1n9_be6031da}
```

## Key Idea

The key to solving this challenge was realizing that the disk image was just
a FAT32 filesystem and that the flag could be hidden in plain text inside the
raw data. Instead of mounting the image or using heavy forensic tools, a
simple `strings` search was enough to locate the flag quickly.

Lesson learned: always try the simplest approaches (like `file` and `strings`)
first before moving to more advanced analysis tools.


   
