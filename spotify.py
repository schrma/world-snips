#
# Use the Spotify Web Connect API using credentials auth code and tokens.
#

import json
import requests
import time
import urllib
import sys
from myopenhab import openhab
from myopenhab import mapValues
from myopenhab import getJSONValue


#   API Gateway
ACCOUNT_URL = 'https://accounts.spotify.com/api/token'
API_ROOT_URL = 'https://api.spotify.com/v1/me/player/'
REDIRECT_URI = 'http://10.0.5.129:8080/static/spotify-auth.html'
VOL_INCREMENT = 10

class spotify(object):
    """
    
    A wrapper for the Spotify Web Connect API

    https://developer.spotify.com/web-api/web-api-connect-endpoint-reference/

    """
    def __init__(self):

        self.debug = True 
        self.oh = openhab()

        self.client_id = self.oh.getState('spotify_client_id')
        self.client_secret = self.oh.getState('spotify_client_secret')
        self.access_token = self.oh.getState('spotify_access_token')
        self.refresh_token = self.oh.getState('spotify_refresh_token')
        self.token_issued = self.oh.getState('spotify_token_issued')
        self.token_expiry = self.oh.getState('spotify_token_expiry')

        if(self.token_expiry == "NULL"):
            self.refreshCredentials()
        if (self.access_token == "NULL"):
            self.generateCredentials()
        else:
            if (time.time() > float(self.token_expiry)):
                self.refreshCredentials()
      
    def generateCredentials(self):
        """
        Generate auth and refresh token for the very first time.
        """

        #   Send OAuth payload to get access_token
        payload = { 'code':self.oh.getState('spotify_auth_code'), 'client_id':self.client_id, 'client_secret':self.client_secret, 'redirect_uri':REDIRECT_URI, 'grant_type':'authorization_code' }
        

        try:
            r = requests.post(ACCOUNT_URL, data=payload, allow_redirects=False)

            resp = r.json()

            if(r.status_code == 200):
                access_token = resp['access_token']
                refresh_token = resp['refresh_token']
                expires_in = resp['expires_in']

                #   Set and Save the access token
                self.access_token = access_token
                self.refresh_token = refresh_token
                self.token_expiry = time.time() + float(expires_in)
                self.token_issued = time.strftime("%Y-%m-%dT%H:%M:%S")
                self.saveCredentials()

        except:
            pass

    def refreshCredentials(self):
        """
        If previous auth token expired, get a new one with refresh token.
        """

        #   Send OAuth payload to get access_token
        payload = { 'refresh_token':self.refresh_token, 'client_id':self.client_id, 'client_secret':self.client_secret, 'redirect_uri':REDIRECT_URI, 'grant_type':'refresh_token' }
        

        try:
            r = requests.post(ACCOUNT_URL, data=payload, allow_redirects=False)

            resp = r.json()

            if(r.status_code == 200):
                access_token = resp['access_token']
                expires_in = resp['expires_in']
                if('refresh_token' in resp): 
                    refresh_token = resp['refresh_token']
                    self.refresh_token = refresh_token

                #   Set and Save the access token
                self.access_token = access_token
                self.token_expiry = time.time() + float(expires_in)
                self.token_issued = time.strftime("%Y-%m-%dT%H:%M:%S")
                self.saveCredentials()

        except:
            pass

    def saveCredentials(self):
        """
        Save current tokens to the openhab.
        """

        self.oh.sendCommand('spotify_access_token',self.access_token)
        self.oh.sendCommand('spotify_refresh_token',self.refresh_token)
        self.oh.sendCommand('spotify_token_expiry',self.token_expiry)
        self.oh.sendCommand('spotify_token_issued',self.token_issued)

    def call(self, path, mode=None, payload=None):
        """
        Call the API at the given path.
        """
        
        if (time.time() > float(self.token_expiry)):
            self.refreshCredentials()
        headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json" }
        if mode == "POST":
            r = requests.post(API_ROOT_URL + path,  headers=headers, data=payload)
            if(r.status_code < 200 and r.status_code > 299):
                pass
            return r.status_code
        elif mode == "PUT":
            r = requests.put(API_ROOT_URL + path,  headers=headers, data=payload)
            if(r.status_code < 200 and r.status_code > 299):
                pass
            return r.status_code
        else:
            r = requests.get(API_ROOT_URL + path,  headers=headers)
            return r.json()

    def update(self):
        """
        Get a current player state.
        """
        try:
            resp = self.call("")
            if ('item' in resp):

                self.oh.sendCommand('spotify_current_track', getJSONValue(resp, ['item','name']))
                self.oh.sendCommand('spotify_current_artist', getJSONValue(resp, ['item', 'artists', 0, 'name']))
                self.oh.sendCommand('spotify_current_cover', getJSONValue(resp, ['item', 'album', 'images', 1, 'url']))
                self.oh.sendCommand('spotify_current_duration', getJSONValue(resp, ['item', 'duration_ms']))
                self.oh.sendCommand('spotify_current_progress', getJSONValue(resp, ['progress_ms']))
                self.oh.sendCommand('spotify_current_playing', mapValues(getJSONValue(resp, ['is_playing']), { 'True': 'ON', 'False': 'OFF' }))
                self.oh.sendCommand('spotify_current_device', getJSONValue(resp, ['device', 'name']))
                self.oh.sendCommand('spotify_current_volume', getJSONValue(resp, ['device', 'volume_percent']))
                self.oh.sendCommand('spotify_current_context_uri', getJSONValue(resp, ['context', 'uri']))
                self.oh.sendCommand('spotify_current_device_id', getJSONValue(resp, ['device', 'id']))

                duration = getJSONValue(resp, ['item', 'duration_ms'])
                progress = getJSONValue(resp, ['progress_ms'])
                if(duration is not None and progress is not None):
                    progress_percent = round(float(progress) / float(duration) * 100,2)
                else:
                    progress_percent = 0

                self.oh.sendCommand('spotify_current_progress_percent', progress_percent)

            else:
                pass
        except:
            resp = ""

        return resp

    def getDevices(self):
        """
        Get List of Devices
        """
        try:
            resp = self.call("devices")
            resp = json.dumps(resp["devices"])
            self.oh.sendCommand('spotify_device_list',resp)
        except:
            resp = ""

        return resp

    def transferPlayback(self):
        """
        Transfer Playback from one device to another
        """

        deviceID = self.oh.getState('spotify_current_device_id')

        payload = json.dumps({ 'device_ids': [ deviceID ] })

        try:
            resp = self.call("","PUT", payload = payload)
            self.update()  
        except:
            resp = ""

        return resp    

    def volumeUp(self):
        """
        Volume up by 10%
        """
        try:
            vol = int(self.oh.getState('spotify_current_volume'))
            vol = int(round(vol/10)*10 + VOL_INCREMENT)
            if(vol>100): 
                vol = 100
            resp = self.call("volume?volume_percent=" + str(vol),"PUT" )
            self.oh.sendCommand('spotify_current_volume',vol)
        except:
            resp = ""

        return resp

    def volumeDown(self):
        """
        Volume down by 10%
        """
        try:
            vol = int(self.oh.getState('spotify_current_volume'))
            vol = int(round(vol/10)*10 - VOL_INCREMENT)
            if(vol<0): 
                vol = 0
            resp = self.call("volume?volume_percent=" + str(vol),"PUT" )
            self.oh.sendCommand('spotify_current_volume',vol)
        except:
            resp = ""

        return resp

    def pause(self):
        """
        Pause player
        """
        try:
            resp = self.call("pause","PUT")
            self.oh.sendCommand('spotify_current_playing',"OFF")
        except:
            resp = ""

        return resp    

    def play(self, context_uri = None):
        """
        Resume player
        """

        deviceID = self.oh.getState('spotify_current_device_id')
        if (deviceID == ''):
            command = "play"
        else:
            command = "play?device_id=" + deviceID

        if (context_uri is None):
            payload = {}
        else:
            payload = json.dumps({ 'context_uri': context_uri })

        try:
            resp = self.call(command,"PUT", payload = payload)
            self.update()  
        except:
            resp = ""

        return resp        

    def previous(self):
        """
        Skip to previous track
        """
        try:
            resp = self.call("previous","POST")
            self.update()  
        except:
            resp = ""

        return resp        

    def next(self):
        """
        Skip to next track
        """
        try:
            resp = self.call("next","POST")
            self.update()
        except:
            resp = ""

        return resp

    def updateConnectionDateTime(self):
        self.oh.sendCommand('spotify_lastConnectionDateTime',time.strftime("%Y-%m-%dT%H:%M:%S+0000",time.gmtime(time.time())))     

def main():

    t1 = time.time()

    c = spotify()

    args = sys.argv
    
    if(len(args) == 1):
        c.update()
    else:

        if(args[1] == "get_devices"):
            c.getDevices()
        if(args[1] == "transfer_playback"):
            c.transferPlayback()
        if(args[1] == "volume_up"):
            c.volumeUp()
        if(args[1] == "volume_down"):
            c.volumeDown()
        if(args[1] == "play"):
            if(len(args)>2):
                a = ""
                for x in range(2, len(args)):
                    a = a + args[x] + " "
                c.play(a.strip())
            else:
                c.play()
        if(args[1] == "pause"):
            c.pause()
        if(args[1] == "previous"):
            c.previous()
        if(args[1] == "next"):
            c.next()

    c.updateConnectionDateTime()

    t2 = time.time()

if __name__ == '__main__':
    main()
