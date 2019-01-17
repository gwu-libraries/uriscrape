import argparse
import datetime
from pdfminer.high_level import extract_text_to_fp
import requests
import io
import os
import sys
import csv
import re
import nltk
from urllib.parse import urlparse, unquote

nltk.download('punkt')


def extract_text(pdf_filepath):
    with open(pdf_filepath, "rb") as fp:
        text_fp = io.StringIO()
        extract_text_to_fp(fp, text_fp)
        return text_fp.getvalue()


def unshorten(url):
    """Don't try to guess; just resolve it, and follow 301s"""
    status = ''
    try:
        h = requests.get(url)
        stack = [i.url for i in h.history]
        stack.append(h.url)
        stack = stack[-1]  # Just keep the last one
    except Exception as e:
        if type(e).__name__ is 'ConnectionError':
            errorstring = e.args[0].args[0]
            hostpos = errorstring.find('host=')
            portpos = errorstring.find(', port=')
            withurlpos = errorstring.find('exceeded with url: ')
            causedbypos = errorstring.find(' (Caused')
            stack = unquote('http://' + errorstring[(hostpos+6):(portpos-1)] + errorstring[(withurlpos+19):(causedbypos)])
            status = 'ConnectionError'
        else:
            stack = ''
            status = type(e).__name__
    return stack, status


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


def urltype(url):
    """ return type and hashtag (if present) """
    u = unquote(url.lstrip('(').rstrip(')'))
    if u.startswith('https://telegram.me/joinchat') \
            or u.startswith('https://t.me/joinchat') \
            or u.startswith('tg://join?invite'):
        return 'tg_joinlink',''
    # any other telegram.me
    if u.startswith('https://web.telegram.org/#/im?p='):
        return 'tg_channel_id',''
    if u.startswith('https://telegram.me') \
            or u.startswith('https://t.me') \
            or u.startswith('tg://resolve?domain='):
        return 'tg_account',''
    if u.startswith('tg://search_hashtag'):
        return 'tg_hashtag',u[28:]
    if 'web.telegram.org' in u \
            or 'telegram.org' in u \
            or 'telegram.me' in u \
            or u.startswith('tg://'):
        return 'tg_other',''

    return 'external',''


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
        csvout.writerow(['File','Access_Date','URL', 'Unshortened URL', 'Status', 'Type', 'Hashtag', 'Domain', 'Primary_Secondary'])
        for m_transcript_filepath in m_transcript_filepaths:
            print('Processing {}'.format(m_transcript_filepath))
            m_transcript_text = extract_text(m_transcript_filepath)
            # outfile.write(m_transcript_text)
            # m_transcript_words = tokenize(m_transcript_text)

            # A pretty good regex for finding URLs in Telegram transcripts
            regex = '[\(]?(https|http|tg):(\/\/)[^\s\(\)]+[\)]?'
            # dateregex = '(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)(, )(January|February|March|April|May|June|July|August|September|October|November|December)( )[0-9]?[0-9](, 20)[0-2][0-9]'
            matches = re.finditer(regex, m_transcript_text, re.MULTILINE)
            filename = os.path.basename(m_transcript_filepath)
            lasturl = ''
            for m in matches:
                print(m.group())
                url = m.group()
                expanded_url = ''
                url_domain = ''
                status = ''
                extract_date = datetime.datetime.now().strftime("%m/%d/%y %H:%M:%S")
                cleaned_url = url.lstrip('(').rstrip(')')
                if cleaned_url == lasturl:
                    # skip if successive URLs are exactly identical
                    continue
                if cleaned_url.lstrip('tg://join?invite=') == lasturl.lstrip('https://telegram.me/joinchat/'):
                    continue
                if cleaned_url.lstrip('tg://resolve?domain=') == lasturl.lstrip('https://telegram.me/'):
                    continue
                lasturl = cleaned_url
                if url.startswith('(http') or url.startswith('http'):
                    expanded_url, status = unshorten(cleaned_url)
                    if expanded_url is '':  # like if it couldn't reach the site
                        # Then just stick with the original URL
                        url_domain = domain(cleaned_url)
                    else:
                        # Use the expanded URL
                        url_domain = domain(expanded_url)
                utype, hashtag = urltype(expanded_url or url) # if expanded_url isn't empty, use it; otherwise use url
                csvout.writerow([filename, extract_date, unquote(url), unquote(expanded_url), status, utype, hashtag, url_domain, primary_secondary(url_domain)])