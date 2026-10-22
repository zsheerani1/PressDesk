# Sample files for testing PressDesk

All text in these files is original and was written for this project.

| File | What it tests | What should happen |
|---|---|---|
| `the-tide-clock.txt` | A .txt file with headings written in different ways ("Chapter One", "CHAPTER 2: …", "Chapter 3 – …", "Chapter IV") | Uploaded with **4 chapters** |
| `salt-and-ash.docx` | A Word file whose chapter titles use the **Heading 1** style (they don't start with "Chapter") | Uploaded with **4 chapters** |
| `the-glasshouse-winter.pdf` | A PDF. PDFs have no heading styles, so it is split on its "Chapter 1: …" lines | Uploaded with **3 chapters** |
| `no-chapter-headings.txt` | A file with no chapter headings | Uploaded as **1 chapter** called "Full manuscript" |
| `empty.txt` | An empty file | Error: "The file you chose is empty." |

## Other things to try

- **Wrong file type:** upload any image (for example a .png or .jpg).
  Error: "Only .docx, .txt and .pdf files can be uploaded."
- **Scanned PDF:** a PDF that is only pictures of pages has no text to
  read. Error: "No text could be found in this PDF…"
- **File too large:** make a 6 MB text file and upload it. Error: "The
  file is too large. The maximum size is 5 MB." To make one, run this
  from the project folder:

  ```
  python -c "open('samples/too-big.txt', 'w').write('words ' * 1100000)"
  ```

  (Delete `too-big.txt` afterwards; it isn't meant to be committed.)
