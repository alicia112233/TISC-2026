# Level 1: REDACTED

## Challenge Information
- **Event**: TISC 2026
- **Level**: Level 1
- **Category**: Forensics / Document Security

## Description
> As part of ongoing transparency efforts, files containing information on The Singularity's whereabouts will be declassified and released to the public. Rest assured that any sensitive information will be redacted to protect active investigations, innocent people, and matters of security.

---

## Challenge Files
- [`TISC-26-091-SINGULARITY.pdf`]: "HEADQUARTERS // ANALYTICAL NOTE 26-091 RESTRICTED // EYES ONLY MERIDIAN DIRECTORATE ANALYTICAL CELL", a 5-page declassified investigative document describing The Singularity's operations, criminal plans, and meeting habits.

---

## Vulnerability Analysis
The document contains several redactions intended to obscure sensitive intelligence regarding The Singularity. However, typical improper redaction occurs when visual black rectangles (annotations or drawing paths) are layered directly on top of selectable text streams without flattening, rasterizing, or stripping the underlying character objects from the PDF structure.

Because the underlying text streams were left intact in the PDF content stream, anyone can inspect or extract the full unredacted text using standard text extraction utilities.

---

## Solution Walkthrough

### 1. Extracting Text from the PDF
Using Python's `pypdf` (or command-line tools such as `pdftotext` / `strings`):

```python
import pypdf

reader = pypdf.PdfReader('TISC-26-091-SINGULARITY.pdf')
for i, page in enumerate(reader.pages):
    print(f"=== PAGE {i + 1} ===")
    print(page.extract_text())
```

### 2. Identifying Section 6
On Page 2, under **Section 6 ("The Flag")**, the report describes:

> **6 The Flag**  
> During a search of material associated with one of the group's meeting locations, investigators recovered a curious text fragment.  
> It appeared repeatedly in notes, test files and one unfinished message.  
> `VElTQ3tCUk8hUmVkYWN0UERGc1Byb3Blcmx5TGFoISEhfQ==`  
> The significance of the string remains uncertain.  
> Members appear to regard it as some kind of identifier, challenge, or private joke.

### 3. Base64 Decoding
The recovered string is standard Base64:

```python
import base64
print(base64.b64decode('VElTQ3tCUk8hUmVkYWN0UERGc1Byb3Blcmx5TGFoISEhfQ==').decode())
```

Output:
```text
TISC{BRO!RedactPDFsProperlyLah!!!}
```

---

## Flag
```text
TISC{BRO!RedactPDFsProperlyLah!!!}
```

---

## Key Takeaway
Drawing visual black boxes over sensitive data in a PDF document does not destroy or sanitize the text layer. True redaction requires using specialized redaction tools that permanently remove underlying vector, image, and font stream data before publication.