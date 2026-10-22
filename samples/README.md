# Sample files for testing PressDesk

These files are for trying out the upload and chapter-splitting
features. The books are in the public domain and come from
[Project Gutenberg](https://www.gutenberg.org/), with the Gutenberg
licence text and contents lists removed for ease of use.

| File | Book | What it tests | What should happen |
|---|---|---|---|
| `frankenstein.pdf` | *Frankenstein*, Mary Shelley | A PDF split on its "Chapter 1", "Chapter 2"… lines. The book opens with four letters before Chapter 1. | Uploaded with **[n] chapters**, with the letters kept together as "Opening pages" |
| `alice-in-wonderland.docx` | *Alice's Adventures in Wonderland*, Lewis Carroll | A Word file whose chapter titles use the **Heading 1** style and don't start with "Chapter" (e.g. "Down the Rabbit-Hole") | Uploaded with **[n] chapters** |
| `im-bernsteinwald.txt` | *Im Bernsteinwald*, Wilhelm Bölsche (1927) | A German text with no English "Chapter" headings | Uploaded as **1 chapter** called "Full manuscript" |
| `empty.txt` | — | An empty file | Error: "The file you chose is empty." |

Different heading styles ("Chapter One", "CHAPTER 2: …", "Chapter IV")
are checked by the automated tests in `tests/test_chapters.py`.

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
