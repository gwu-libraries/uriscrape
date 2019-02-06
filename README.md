# uriscrape
Scrapes URIs from Telegram channel transcripts in PDF files.  Typically URIs will take the form of something like these examples:
```
https://t.me/joinchat/AAAAAEOs3wFD4Mv6SN4hlQ

(tg://join?invite=AAAAAEOs3wFD4Mv6SN4hlQ)

https://drive.google.com/open?id=0B_3xyna6XV4GMHNPU0VVWHZKRXc

https://archive.org/details/Rumiyah13UR_201709
(https://archive.org/details/Rumiyah13UR_201709)

(tg://search_hashtag?hashtag=%D8%A6%DB%95%D9%84%DA%BE%D8%A7%D9%8A%D8%A7%D8%AA)
```

## Running the program

```
usage: `python uriscrape.py transcript`

positional arguments:
  transcript         filepath to transcript pdf or directory

optional arguments:
  None yet...

```

## Output file

**`urls.xlsx`** - All found URIs, including columns/variables as follows:
- *File*: PDF file processed
- *Access_Date*: Date/time the program was run. May be important for documenting when the program attempted to resolve URIs
- *Post_Date*: Date of the post, as derived from the date labels in the Telegram transcript
- *URL*: URL as found
- *Site_Reached*: True/False - whether the URI was able to be resolved
- *Unshortened URL*: Unshortened URL (e.g.  https://youtu.be/lqXwyl89xU4 -> unshortens to https://www.youtube.com/watch?v=lqXwyl89xU4&feature=youtu.be )
- *Status*: Error code, if an error was encountered in trying to access the URI
- *Type*: Classification of the link
- *Hashtag*: Hashtag, if the link is a Telegram hashtag link
- *Channel*: Channel, if the link is a Telegram join link
- *Account*: Account, if the link is a Telegram account link
- *Domain*: Full server daomain (e.g. www.youtube.com)
- *Primary_Secondary*: Just the primary and secondary portions of the domain (e.g. youtube.com)
