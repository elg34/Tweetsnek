import tweepy
import json
from multiprocessing import Process
from pathlib import Path
import time
import sys

# Auth keys and secrets
consumer_key = 'XXXXXXXXXXX'
consumer_secret = 'XXXXXXXXXXX'
access_token = 'XXXXXXXXXXX'
access_token_secret = 'XXXXXXXXXXX'

USERCTL = 'XXXXXXXXXXX'         # twitter user that can send control signals
USERID = 00000000               # twitter id of that user
PARSESIG = 'XXXXXXXXX'          # parse USERCTL's tweets for signal to change tweepy filter
TPERFILE = 100                  # how many tweets per file to save
KWFILE = 'kw.txt'               # get file for keywords

## CONTROL TWEET FORMAT
## PARSESIG {replace/add/remove/stop} {optional: KW1::KW2}

class MyTweetListener(tweepy.StreamListener):
        def __init__(self,kw):
                print('Initializing Stream of Tweets...')
                print('Now tracking:',' '.join(kw))
                self.tcount = 0 # current number of tweets in file
                self.max_tw = TPERFILE
                self.filename = None
        
        def on_data(self, data):
                tweet = json.loads(data) # load tweet data
                #print('@%s: %s' % (tweet['user']['screen_name'], tweet['text'])) # print tweet in console
                
                # increment counter for file name change
                self.tcount += 1
                print(self.tcount,'/',self.max_tw,':',tweet['user']['screen_name'])
                if self.tcount > self.max_tw:
                        print('If statement called!',self.tcount)
                        self.filename = 'data/'+time.strftime("%Y%m%d-%H%M%S") + '.txt'
                        self.tcount=0
                
                # save tweet
                if  self.filename is None:
                        self.filename='data/'+time.strftime("%Y%m%d-%H%M%S") + '.txt'
                if Path(self.filename).is_file():
                        filemode = 'a'
                else:
                        filemode = 'w'
                        print('Creating file',self.filename)
                with open(self.filename, mode=filemode, encoding='utf-8') as fl:
                        json.dump(tweet, fl, sort_keys = True)
                        fl.write('\n')

        def on_error(self, status):
                print(status)
                if status == 420:
                        print('Too many connection attempts in tweet stream!')
                        return False #returning disconnects the stream
                
class MyUserListener(tweepy.StreamListener):
        def __init__(self, kw):
                print('Initialising User DM stream...')
                self.run = True # Variable to stop whole script from DM
        
        def on_data(self, data):
                if 'direct_message' in data:
                        dm = json.loads(data) # load tweet data
                        print('Received signal DM: ',dm['direct_message']['text'])
                        # check if tweet is command to change keywords in tweet stream
                        if USERCTL in dm['direct_message']['sender']['screen_name'] and PARSESIG in dm['direct_message']['text']:
                                parse = self.parsemsg(dm['direct_message']['text'])
                                if not parse:
                                        print('Stop signal received, else could not parse DM syntax! Did not change keywords.')
                                else:
                                        print('Successfully parsed DM. Quitting DM stream.')
                                        return False #returning disconnects the stream
                        else:
                                print('Note: Received unrelated DM!')
                                
        def parsemsg(self,msg):
                msg = msg.split(' ')
                success = False
                if msg[0]!=PARSESIG: # if first word is not the codeword
                        print('Error in message syntax! First word not keyword.')
                        return False
                if len(msg)<3 or (len(msg)==2 and msg[1]!='stop'):
                        print('Error in message syntax! Not enough arguments in message.')
                        return False
                
                newkws = None if msg[1]=='stop' else msg[2].split('::')
                        
                if msg[1] == 'replace': # delete original keyword list (except codeword) and add all specified keywords
                        del kw[1:] 
                        for k in newkws:
                                kw.append(k)
                        success = True
                elif msg[1] == 'add': # add all specified keywords
                        for k in newkws:
                                kw.append(k)
                        success = True
                elif msg[1] == 'remove': # remove all specified keywords from global keyword list (if they exist in the list)
                        for k in newkws:
                                for ki in range(1,len(kw)):
                                        if k == kw[ki]:
                                                kw.pop(ki)
                                                break
                        success = True
                elif msg[1] == 'stop':
                        self.run = False
                        print('DM stream received stop signal!')
                        success = True
                else:
                        print('Error in message syntax! Second word not interpretable.')
                        success = False
                return success
                                        
        def on_error(self, status):
                print(status)
                if status == 420:
                        print('Too many connection attempts in DM stream!')
                        return False #returning disconnects the stream


if __name__ == '__main__':

        # Authentification
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        
        # initialise keyword list with signal for kw parser
        kw = list([PARSESIG])
        
        # if script has previously been aborted, load keywords from previous file
        if Path(KWFILE).exists():
                with open(KWFILE, 'r') as fp:  
                        line = fp.readline()
                        while line:
                                kw.append(line.rstrip())
                                line = fp.readline()
        
        # API for DM returns
        api = tweepy.API(auth)
        
        # listeners and stream for filtered tweets and user dm's respectively
        tweetstream = tweepy.Stream(auth, MyTweetListener(kw))
        userstream = tweepy.Stream(auth, MyUserListener(kw))
        
        print('Script ready, waiting for commands! Syntax: ' + kw[0] + ' {replace/add/remove/stop} {optional: KW1::KW2}')
        api.send_direct_message(user_id = USERID, text = 'Script ready, waiting for commands! Syntax: ' + kw[0] + ' {replace/add/remove/stop} {optional: KW1::KW2}')
        while userstream.listener.run:
                p = Process(target = tweetstream.filter, kwargs = dict(track=kw)) # setup
                p.start()
                userstream.userstream() # keep monitoring for keyword change or stop signal, blocking call
                api.send_direct_message(user_id = USERID, text = 'New keywords: '+' '.join(kw))
                print('New keywords: '+' '.join(kw))
                with open(KWFILE, 'w') as fp:  
                        for i in kw[1:]:
                                fp.write(i+'\n')
                #print(tweetstream.listener.tcount,':',tweetstream.listener.filename) # killing the process messes with these paraeters -> I think they just get reset
                p.terminate() # sad way to end, but twitter doesnt give me a choice
        api.send_direct_message(user_id = USERID, text = 'Script dying... send help...')
        print('Exiting script...')
