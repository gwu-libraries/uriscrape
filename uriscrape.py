import argparse
from pdfminer.high_level import extract_text_to_fp
import requests
import io
import os
import sys
import csv
import re
import nltk
from urllib.parse import urlparse

nltk.download('punkt')


def extract_text(pdf_filepath):
    with open(pdf_filepath, "rb") as fp:
        text_fp = io.StringIO()
        extract_text_to_fp(fp, text_fp)
        return text_fp.getvalue()


def unshorten(url):
    """Don't try to guess; just resolve it, and follow 301s"""
    try:
        h = requests.get(url)
        stack = [i.url for i in h.history]
        stack.append(h.url)
        stack = stack[-1]  # Just keep the last one
    except:
        stack = ''
    return stack


def domain(url):
    """ Pull out just the server domain part as a list """
    return urlparse(url).netloc


def primary_secondary(url):
    """ return just the secondary.primary domain part, as a single string """
    if len(url) >= 2:
        url_split = url.split('.')
        url_join = '.'.join(url_split[-2:])
        return url_join
    # To consider: Would a single-length case ever happen?
    else:
        return url


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('transcript', help='filepath to transcript pdf or directory')

    args = parser.parse_args()

    # Compose m_transcript_filepaths list
    if not os.path.exists(args.transcript):
        print('{} does not exist'.format(args.transcript))
        sys.exit(1)
    m_transcript_filepaths = []
    if os.path.isdir(args.transcript):
        for filename in os.listdir(args.transcript):
            filepath = os.path.join(args.transcript, filename)
            if os.path.isfile(filepath) and filename.lower().endswith('.pdf'):
                m_transcript_filepaths.append(filepath)
    else:
        m_transcript_filepaths.append(args.transcript)

    with open("urls.csv", "w") as outfile:
        csvout = csv.writer(outfile)
        csvout.writerow(['URL', 'Unshortened URL', 'Domain', 'Primary_Secondary'])
        for m_transcript_filepath in m_transcript_filepaths:
            print('Processing {}'.format(m_transcript_filepath))
            m_transcript_text = extract_text(m_transcript_filepath)
            # outfile.write(m_transcript_text)
            # m_transcript_words = tokenize(m_transcript_text)

            # A pretty good regex for finding URLs in Telegram transcripts
            regex = '[\(]?(https|http|tg):(\/\/)[^\s\(\)]+[\)]?'
            matches = re.finditer(regex, m_transcript_text, re.MULTILINE)
            for m in matches:
                print(m.group())
                url = m.group()
                expanded_url = ''
                url_domain = ''
                if url.startswith('(http') or url.startswith('http'):
                    cleaned_url = url.lstrip('(').rstrip(')')
                    expanded_url = unshorten(cleaned_url)
                    if expanded_url is '':  # like if it couldn't reach the site
                        # Then just stick with the original URL
                        url_domain = domain(cleaned_url)
                    else:
                        # Use the expanded URL
                        url_domain = domain(expanded_url)
                csvout.writerow([url] + [expanded_url] + [url_domain] + [primary_secondary(url_domain)])