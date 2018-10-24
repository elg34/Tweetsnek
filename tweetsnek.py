import tweepy
import json
from multiprocessing import Process,Value,Queue
from pathlib import Path
import time
import sys
import logging
import numpy as np

logging.basicConfig(filename='error.log')

settings = {
        'USERCTL':'ENTER USER HERE',         # twitter user that can send control signals
        'USERID': 99999,              # twitter id of that user
        'PARSESIG':'TpyChange',          # parse USERCTL's tweets for signal to change tweepy filter
        'TPERFILE':100,                  # how many tweets per file to save
        'KWFILE':'kw.txt',               # keyword file
        'AUTHFILE':'auth.txt',           # authentification file
        'HISTFILE':'hist.txt',           # history file
        'MAX_CON':5,                     # number of reconnection attempts allowed
        'CON_RESET':1                    # time after which reconnection attempts resets in hours
}

class MyTweetListener(tweepy.StreamListener):
        'Class is used for monitoring tweets, inheriting from the StreamListener class. Incoming tweets are saved in the /data folder.'
        def __init__(self,tperfile):
                print('Initializing Stream of Tweets...')
                self.tcount = 0 # current number of tweets in file
                self.max_tw = tperfile
                self.filename = None
        
        def on_data(self, data):
                tweet = json.loads(data) # load tweet data
                #print('@%s: %s' % (tweet['user']['screen_name'], tweet['text'])) # print tweet in console
                
                # increment counter for file name change
                self.tcount += 1
                
                # printouts
                if 'user' in tweet and 'screen_name' in tweet['user']:
                    print(self.tcount,'/',self.max_tw,':',tweet['user']['screen_name'])
                
                if 'extended_tweet' in tweet and 'full_text' in tweet['extended_tweet']:
                        print(tweet['extended_tweet']['full_text'])
                elif 'retweeted_status' in tweet and 'extended_tweet' in tweet['retweeted_status'] and 'full_text' in tweet['retweeted_status']['extended_tweet']:
                        print(tweet['retweeted_status']['extended_tweet']['full_text'])
                else:
                        print(tweet['text'])
                
                # maximum file size reached
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
                raise Exception('Error in tweet stream:'+str(status))
                
class MyUserListener(tweepy.StreamListener):
        'Class is used for monitoring the controller\'s handle, inheriting from the StreamListener class. Incoming DMs are parsed for tweetsnek commands.'
        def __init__(self,userctl,parsesig,kwfile,histfile):
                print('Initialising User DM stream...')
                self.stop = False # Variable to stop whole script from DM
                self.kw = load_kw(parsesig,kwfile)
                self.userctl = userctl
                self.parsesig = parsesig
                self.kwfile = kwfile
                self.histfile = histfile
        
        def on_data(self, data):
                if 'direct_message' in data:
                        dm = json.loads(data) # load tweet data
                        print('Received signal DM: ',dm['direct_message']['text'])
                        # check if tweet is command to change keywords in tweet stream
                        if self.userctl in dm['direct_message']['sender']['screen_name'] and self.parsesig in dm['direct_message']['text']:
                                parse = self.parsemsg(dm['direct_message']['text'])
                                if not parse:
                                        print('Stop signal received, else could not parse DM syntax! Did not change keywords.')
                                        if self.stop:
                                                return False # disconnects the stream
                                else:
                                        print('Successfully parsed DM. Quitting DM stream.')
                                        mode = 'a' if Path(self.histfile).exists() else 'w'
                                        with open(self.histfile,mode) as hf:
                                                hf.write(time.strftime("%Y%m%d-%H%M%S") + '::' + dm['direct_message']['text'] + '\n')
                                        print('New keywords: '+' '.join(self.kw))
                                        with open(self.kwfile, 'w') as fp:  
                                                for i in self.kw[1:]:
                                                        fp.write(i+'\n')
                                        return False # disconnects the stream
                        else:
                                print('Note: Received unrelated DM!')
                                
        def parsemsg(self,msg):
                msg = msg.split(' ')
                success = False
                if msg[0]!=self.parsesig: # if first word is not the codeword
                        print('Error in message syntax! First word not keyword.')
                        return False
                if len(msg)<2 or (len(msg)==2 and msg[1]!='stop'):
                        print('Error in message syntax! Not enough arguments in message.')
                        return False
                
                newkws = None if msg[1]=='stop' else msg[2].split('::')
                        
                if msg[1] == 'replace': # delete original keyword list (except codeword) and add all specified keywords
                        del self.kw[1:] 
                        for k in newkws:
                                self.kw.append(k)
                        success = True
                elif msg[1] == 'add': # add all specified keywords
                        for k in newkws:
                                self.kw.append(k)
                        success = True
                elif msg[1] == 'remove': # remove all specified keywords from global keyword list (if they exist in the list)
                        for k in newkws:
                                for ki in range(1,len(self.kw)):
                                        if k == self.kw[ki]:
                                                self.kw.pop(ki)
                                                break
                        success = True
                elif msg[1] == 'stop':
                        self.stop = True
                        print('DM stream received stop signal!')
                        success = False
                else:
                        print('Error in message syntax! Second word not interpretable.')
                        success = False
                return success
                                        
        def on_error(self, status):
                raise Exception('Error in DM stream:'+str(status))


def load_kw(parsersig,kwfile):
        'Load monitored keywords used for the tweetstream.'
        keywords = list([parsersig]) # initialise keyword list with signal for kw parser
        if Path(kwfile).exists(): # if script has previously been aborted, load keywords from previous file
                with open(kwfile, 'r') as fp:  
                        line = fp.readline()
                        while line:
                                keywords.append(line.rstrip())
                                line = fp.readline()
        return keywords

def get_keys(authfile):
        'Load keys for authentification.'
        if Path(authfile).exists():
                        with open (authfile, "r") as f:
                                cred=f.readlines()
                        cred = [i.rstrip() for i in cred]
        else:
                raise Exception('Missing authentification file!')
        return cred

def make_msg(t,u):
        event = {
                "event": {
                        "type": "message_create",
                        "message_create": {
                        "target": {
                                "recipient_id": u
                                },
                        "message_data": {
                                "text": t
                                }
                        }
                }
        }
        return event

def run_tstream(auth,settings,kw,q):
        'Function for tweetstream process. Puts error in queue if stream crashes. Returns False when it crashes.'
        tstream = tweepy.Stream(auth, MyTweetListener(settings['TPERFILE']))
        try:
                tstream.filter(track=kw) # setup tweet filter
        except Exception as e:
                q.put(e)
                return e

def run_ustream(auth,settings,errq,stopq):
        'Function for userstream process. Puts error in queue if stream crashes, returns True if stop signal is received.'
        ustream = tweepy.Stream(auth, MyUserListener(settings['USERCTL'],settings['PARSESIG'],settings['KWFILE'],settings['HISTFILE']))
        try:
                ustream.userstream()
                stopq.put(ustream.listener.stop)
                return True
        except Exception as e:
                errq.put(e)
                return False

def setup_snek(settings):
        'Sets up authentification and Twitter API, starts stream processes for monitoring a specific set of keywords.'
        
        ## AUTHENTIFICATION
        keys = get_keys(settings['AUTHFILE']) # get consumer keys, secrets etc, see README
        auth = tweepy.OAuthHandler(keys[0], keys[1]) # use keys to get authentification
        auth.set_access_token(keys[2], keys[3])
        api = tweepy.API(auth) # set up api for messaging
        
        ## SEND WELCOME DM
        errors = list()
        kw = load_kw(settings['PARSESIG'],settings['KWFILE']) # load existing keywords or set up new keywords
        startmesg = 'This is snek! Syntax: ' + kw[0] + ' {replace/add/remove/stop} {optional: KW1::KW2}\n' + 'Currently set keywords: '+' '.join(kw)
        try:
                print(startmesg)
                api.send_direct_message_new(make_msg(startmesg,settings['USERID']))
        except tweepy.TweepError as e:
                errors.append('Error in API:'+str(e))
                pass
        
        ## SETUPSTREAM PROCESSES
        errq = Queue(maxsize=2)
        stopq = Queue(maxsize=1)
        uproc = Process(target = run_ustream, kwargs = dict(auth=auth,settings=settings,errq=errq,stopq=stopq)) # setup userstream process
        tproc = Process(target = run_tstream, kwargs = dict(auth=auth,settings=settings,kw=kw,q=errq)) # setup tweetstream process
        uproc.start()
        tproc.start()
        while True:
                if not tproc.is_alive() or not uproc.is_alive() or not errq.empty() or not stopq.empty():
                        stop=stopq.get() if not stopq.empty() else False
                        while not errq.empty():
                                errors.append(str(errq.get()))
                        break;
        tproc.terminate()
        uproc.terminate()
        
        ## SEND EXIT DM
        if stop:
                exitmesg = 'Exiting script...'
        elif len(errors)>0:
                exitmesg = '::'.join(errors)  + ' Attempting restart (no further commands accepted!)...'
        else:
                exitmesg = 'Attempting restart...'
        try:
                print(exitmesg)
                api.send_direct_message_new(make_msg(exitmesg,settings['USERID']))
        except tweepy.TweepError as e:
                errors.append('Error in API:'+str(e))
                pass
        
        ## REPORT SNEKSTATUS
        return dict(mesgs=errors,stop=stop)

if __name__ == '__main__':
        connection_attempts = 0
        last_connect=time.time()
        restart = True
        error = False
        mins = np.array([1,5,15]) * 60
        while restart and connection_attempts<settings['MAX_CON']:
                print('Connection attempt:',connection_attempts+1)
                snek = setup_snek(settings)
                if snek['stop']:
                        restart=False
                if len(snek['mesgs'])>0 and not snek['stop']:
                        new_connect = time.time()
                        waitforit = mins[connection_attempts] if connection_attempts<len(mins) else max(mins)
                        if new_connect-last_connect<(settings['CON_RESET']*60*60):
                                print('Time since last connect:',new_connect-last_connect)
                                connection_attempts = connection_attempts+1
                        else:
                                last_connect = new_connect
                                connection_attempts = 0
                        print('Sleeping for',waitforit/60,'minutes!')
                        time.sleep(waitforit)
