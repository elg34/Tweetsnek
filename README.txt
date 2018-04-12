TWEETSNEK - Python twitter scraping

To use this code, you will first have to create/choose a twitter account for scraping - this account needs the appropriate permissions from twitter (see https://apps.twitter.com/). We here assume that there is one account to do the scraping and another one that sends the keywords or stop signal, via direct message. 

1. Enter key/token in tweetsnek.py
2. Choose User/User ID of person that can send DM's to control scraping in tweetsnek.py
3. Send commands to control which tweets are saved. Keywords are separated by :: and should not include spaces (e.g. tweeksnek stop, tweetsnek add headline::news).

## CONTROL TWEET FORMAT
PARSESIG {replace/add/remove/stop} {optional: KW1::KW2}

Note: Management of rate limits is not currently implemented
