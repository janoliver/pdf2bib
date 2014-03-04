#!/usr/bin/env python
# -=- encoding: utf-8 -=-

"""
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

    pdf2bib -o mybib.bib -e file,url ~/Library/2006 ~/My_new_paper.pdf

Write output to stdout and analyze ~/Library

    pdf2bib ~/Library

"""


import sys
import os
import subprocess
import re
from urllib import request
import argparse


__author__ = "Jan Oliver Oelerich"
__copyright__ = "Copyright 2014"
__credits__ = ["Jan Oliver Oelerich"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Jan Oliver Oelerich"
__email__ = "janoliver@oelerich.org"
__status__ = "Production"


class BibEntry(object):
    """
    This is a single bibentry. Its members are id, which is the bibtex key,
    type, which is the @type bibtex document type and the values in args.
    """

    parts = re.compile("@(?P<type>[\w\-]+)\{(?P<id>[\w\- ]+), (?P<args>.+)\}")
    keys = re.compile("(?P<key>[\w\-]+)=\{(?P<value>.+?)\}(, |$)")

    def __init__(self, entry):
        """The object is initialized with bibtex code. It is parsed here."""

        match = self.parts.search(entry)
        keys = self.keys.finditer(match.group('args'))

        self.id = match.group('id')
        self.type = match.group('type')
        self.args = dict()

        for m in keys:
            self.args[m.group('key')] = m.group('value')

    def format(self, exclude=list()):
        """Print the bib entry formatted. If keys should be excluded,
        this can be specified with the exclude argument."""

        result = "@{type}{{{key},".format(type=self.type, key=self.id)
        for key, value in self.args.items():
            if key not in exclude:
                result += "\n    {key}={{{value}}}".format(key=key, value=value)
        result += "\n}"

        return result

    def add_arg(self, key, value):
        """Add an argument to the bibtex metadata"""

        self.args[key] = value


class BibLookup(object):
    """This is just a small wrapper class for the dx.doi.org lookup of the
    bibtex entries."""

    url = 'http://dx.doi.org/{doi}'
    headers = {'Accept': 'text/bibliography; style=bibtex'}

    def get_bibtex(self, doi):
        """Return bibtex entry by doi"""

        req = request.Request(self.url.format(doi=doi), headers=self.headers)
        f = request.urlopen(req)
        return f.read().decode('utf-8')


class PDFParser(object):
    """Class to parse PDF files with pdftotext or pdftohtml, which are
    both contained in poppler. It's main purpose is to find the DOI"""

    converters = (
        ['pdftotext', '-l', '1', '{pdf}', '-'],
        ['pdftohtml', '-stdout', '-i', '-l', '1', '{pdf}']
    )

    doi_regex = re.compile(b"10.\d{4}/[\w\-\.]+")

    def __init__(self):
        """Find, which converter is present in the system"""

        for converter in self.converters:
            location = self.which(converter[0])
            if location:
                self.converter = converter
                self.converter[0] = location
                return
        raise Exception()

    def get_doi(self, pdf_file):
        """Find DOI in the PDF and return it."""

        command = [x.format(pdf=pdf_file) for x in self.converter]
        p = subprocess.Popen(command, stdout=subprocess.PIPE)
        out, err = p.communicate()

        match = self.doi_regex.search(out)
        if match:
            return match.group().decode("utf-8")
        else:
            return None

    @staticmethod
    def which(program):
        """Resembles Unix's `which` utility, to check for executables.
        Stolen from Stackoverflow. :)"""

        def is_exe(fpath):
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        fpath, fname = os.path.split(program)
        if fpath:
            if is_exe(program):
                return program
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                path = path.strip('"')
                exe_file = os.path.join(path, program)
                if is_exe(exe_file):
                    return exe_file

        return None


def main(args):
    parser = PDFParser()
    bibtex = BibLookup()

    # gather files to analyze
    f = list()
    for location in args.location:
        if os.path.isfile(location) and ".pdf" in location.tolower():
            f.append(location)
        elif os.path.isdir(location):
            for (path, _, files) in os.walk(location):
                f.extend([os.path.join(path, f) for f in files if ".pdf" in f])

    # iterate the gathered files and add them to the output
    for file in f:
        print("Analyzing {}...".format(file))
        doi = parser.get_doi(file)
        if doi:
            print("  .. Found DOI: {}".format(doi))
            print("  .. Fetching Metadata...")
            b = BibEntry(bibtex.get_bibtex(doi))
            b.add_arg('file', file)
            args.output.write(b.format(exclude=args.exclude.split(",")))
            args.output.write("\n\n")
            print("  .. Wrote Entry. ")
        else:
            print("  !! No DOI found!")


if __name__ == "__main__":
    # some cli arguments...
    ap = argparse.ArgumentParser(description='Generate biblatex from PDFs')
    ap.add_argument('location', nargs='+', type=str,
                    help='List of folders or PDF files')
    ap.add_argument('-o', '--output', nargs='?', type=argparse.FileType('w'),
                    default=sys.stdout,
                    help='Output file. If not specified, print to stdout')
    ap.add_argument('-e', '--exclude', type=str,
                    help='Bibtex keys to exclude from output. E.g., url,file')

    main(ap.parse_args())