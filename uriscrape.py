import argparse
import datetime
from pdfminer.high_level import extract_text_to_fp
import requests
import io
import os
import sys
import re
import nltk
import openpyxl
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
        h = requests.get(url, timeout=10)
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


def lstringstrip(s_orig, s_strip):
    """ Left-strip a whole string, not 'any of these characters' like str.lstrip does """
    if s_orig.startswith(s_strip):
        return s_orig[len(s_strip):]
    else:
        return s_orig


def domain(url):
    """ Pull out just the server domain part as a list """
    nl = urlparse(url).netloc
    if len(nl.split('.')) < 2:
        # we don't want incomplete domains like 'http://www'
        raise ValueError
    return nl


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

    if u.startswith('https://telegram.me/joinchat/'):
        return 'tg_joinlink','',u[29:],''
    if u.startswith('https://t.me/joinchat/'):
        return 'tg_joinlink','',u[22:],''
    if u.startswith('tg://join?invite='):
        return 'tg_joinlink','',u[17:],''
    if u.startswith('https://web.telegram.org/#/im?p='):
        return 'tg_channel_id','','',''
    if u.startswith('https://telegram.me/'):
        return 'tg_account','','',u[20:]
    if u.startswith('https://t.me/'):
        return 'tg_account','','',u[13:]
    if u.startswith('http://t.me/'):
        return 'tg_account', '', '', u[12:]
    if u.startswith('tg://resolve?domain='):
        return 'tg_account','','',u[20:]
    if u.startswith('tg://search_hashtag'):
        return 'tg_hashtag',u[28:],'',''
    if 'web.telegram.org' in u \
            or 'telegram.org' in u \
            or 'telegram.me' in u \
            or u.startswith('tg://'):
        return 'tg_other','','',''

    return 'external','','',''


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

    # wb = openpyxl.Workbook(write_only=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['File','Access_Date','Post_Date','URL', 'Site_Reachable', 'Unshortened URL', 'Status', 'Type', 'Hashtag', 'Channel', 'Account', 'Domain', 'Primary_Secondary'])

    for m_transcript_filepath in m_transcript_filepaths:
        print('Processing {}'.format(m_transcript_filepath))
        m_transcript_text = extract_text(m_transcript_filepath)
        # outfile.write(m_transcript_text)
        # m_transcript_words = tokenize(m_transcript_text)

        # A pretty good regex for finding URLs in Telegram transcripts
        linkregex = '[\(]?(https|http|tg):(\/\/)[^\s\(\)]+[\)]?'
        # Note the ( | ) expressions in dateregex: One of the characters is not the usual space character.
        # It's ord() value is 160, vs. 32 for regular space.  This catches more date matches.
        dateregex = '(Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)(,( | ))(January|February|March|April|May|June|July|August|September|October|November|December)( | )[0-9]?[0-9](,( | )20)[0-2][0-9]'
        regex = '(' + linkregex + '|' + dateregex + ')'
        matches = re.finditer(regex, m_transcript_text, re.MULTILINE)
        filename = os.path.basename(m_transcript_filepath)
        lasturl = ''
        last_date = ''
        last_date_mmddyyyy = None
        for m in matches:
            print(m.group())
            match = m.group()
            # if the match is a date, not a link
            if 'day' in match[3:9]:
                # set the date, then move on to the next match
                last_date = match.replace(' ', ' ')
                last_date_obj = datetime.datetime.strptime(last_date, "%A, %B %d, %Y")
                last_date_mmddyyyy = last_date_obj.strftime("%m/%d/%Y")
                continue

            url = match
            expanded_url = ''
            url_domain = ''
            status = ''
            extract_date = datetime.datetime.now().strftime("%m/%d/%y %H:%M:%S")
            cleaned_url = url.lstrip('(').rstrip(')')
            # if lasturl is too short, some of the tests below will always be true
            if len(lasturl) <= 12:
                lasturl = "This definitely will not match!"
            if cleaned_url == lasturl:
                # skip if successive URLs are exactly identical
                continue
            if cleaned_url.startswith('http') and \
                    lstringstrip(lstringstrip(cleaned_url, 'https://'), 'http://').rstrip('/') == \
                    lstringstrip(lstringstrip(lasturl, 'https://'), 'http://').rstrip('/'):
                # skip if they point to the same endpoint, even with http vs. https protocol, treat as the same. Ignore trailing `'/'
                continue
            if cleaned_url.startswith('tg:join?invite=') and \
                    lstringstrip(cleaned_url, 'tg://join?invite=')[:10] == lstringstrip(lasturl, 'https://telegram.me/joinchat/')[:10]:
                # skip if these are identical out to 10 characters.  This ignores junk that tends to get concatenated on.
                continue
            if cleaned_url.startswith('tg:join?invite=') and \
                    lstringstrip(cleaned_url, 'tg://join?invite=')[:10] == lstringstrip(lasturl, 'https://t.me/joinchat/')[:10]:
                # skip if these are identical out to 10 characters.  This ignores junk that tends to get concatenated on.
                continue
            if cleaned_url.startswith('tg://resolve?domain=') and \
                    lstringstrip(cleaned_url, 'tg://resolve?domain=')[:10] == lstringstrip(lasturl, 'https://telegram.me/')[:10]:
                # skip if these are identical out to 10 characters.  This ignores junk that tends to get concatenated on.
                continue
            if cleaned_url.startswith('tg://resolve?domain=') and \
                    lstringstrip(cleaned_url, 'tg://resolve?domain=')[:10] == lstringstrip(lasturl, 'https://t.me/')[:10]:
                # skip if these are identical out to 10 characters.  This ignores junk that tends to get concatenated on.
                continue
            if cleaned_url.startswith('tg://resolve?domain=') and \
                    lstringstrip(cleaned_url, 'tg://resolve?domain=')[:10] == lstringstrip(lasturl, 'http://t.me/')[:10]:
                # skip if these are identical out to 10 characters.  This ignores junk that tends to get concatenated on.
                continue
            if cleaned_url.startswith('https://web.telegram.org/#/im?p=') and \
                    cleaned_url.startswith('https://web.telegram.org/#/im?p='):
                # skip if this is the channel link that usually appears at the bottom of each page of the PDF
                continue
            lasturl = cleaned_url
            site_reachable = None
            if cleaned_url.startswith('http'):
                try:
                    expanded_url, status = unshorten(cleaned_url)
                    if expanded_url is '':  # like if it couldn't reach the site
                        site_reachable = False
                        # Then just stick with the original URL
                        url_domain = domain(cleaned_url)
                    else:
                        site_reachable = True
                        # Use the expanded URL
                        url_domain = domain(expanded_url)
                except ValueError as ve:
                    # if the URL isn't valid, then skip
                    continue
            utype, hashtag, channel, account = urltype(expanded_url or cleaned_url) # if expanded_url isn't empty, use it; otherwise use url
            # Comment the next `if` block out if debugging - there may be some remaining patterns we want to recategorize.
            if utype == 'tg_hashtag' and hashtag == '':
                # skip empty hashtags
                continue
            if utype == 'tg_other':
                continue
            if utype != 'external':
                site_reachable = ''
            try:
                ws.append([filename, extract_date, last_date_mmddyyyy, unquote(cleaned_url), site_reachable, unquote(expanded_url), status, utype, hashtag, channel, account, url_domain, primary_secondary(url_domain)])
            except openpyxl.utils.exceptions.IllegalCharacterError as e:
                # we're just going to swallow these for now, and skip writing the row
                pass
    wb.save('urls' + datetime.datetime.now().strftime("%Y%m%d_%H%M") + '.xlsx')