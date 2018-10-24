TWEETSNEK - Python twitter scraping

To run this code, you will need access to 2 twitter accounts.

1. Setup scraper account. This account needs the appropriate permissions from twitter (see https://apps.twitter.com/).
   You will have to register an application to receive consumer keys and access tokens (Application settings > manage keys and access tokens).
2. Setup controller account. Choose a twitter account will control the scraper through direct messages.
3. Replace the lines in auth.txt with the appropriate key/token from step 1.
4. Edit the settings dictionnary in tweetsnek.py as needed.
5. Run tweetsnek.py in a console.
5. Send commands to control which tweets are saved. Keywords are separated by :: and should not include spaces.
   Format: PARSESIG {replace/add/remove/stop} {optional: KW1::KW2}
   Examples: tweeksnek stop, tweetsnek add headline::news

Note:
In case tweetsnek encounters an error, attempts will be made to reconnect to twitter.
The time spent between reconnects increases after every failed attempt, up to 15 minutes (1,5,15 minutes).
Connection attempt resets can be controlled in the settings.

%%%% 24/10/2018
- twitter changed the way it deals with sending DM's - for a quick fix in python 3.6.0, checkout the dm_tweepy branch and follow the instructions here to modify your tweepy install:
https://github.com/tweepy/tweepy/issues/1081

binder.py
https://github.com/do-n-khanh/tweepy/commit/c978749edb944394bd412922d0eb30170e0598bf
api.py
https://github.com/do-n-khanh/tweepy/commit/79772c976c64830149095f087c16c181912466ba#diff-ea5dd38a4efd9ff36c96e04ab0597cfb


