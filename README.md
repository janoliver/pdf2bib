# pdf2bib

This script extracts the DOI number (dx.doi.org) from PDF files and
downloads the metadata needed for bibtex entries.

## Dependencies

This script has the following dependencies:

  * pdftotext or pdftohtml, both contained in Poppler

## Usage

Examples:

Find all papers in ~/Library/2006 and add ~/My_new_paper.pdf and write
the output to mybib.bib, excluding the fields file and url.

    pdf2bib.py -o mybib.bib -e file,url ~/Library/2006 ~/My_new_paper.pdf

Write output to stdout and analyze ~/Library

    pdf2bib.py ~/Library