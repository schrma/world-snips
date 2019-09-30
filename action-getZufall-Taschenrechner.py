#!/usr/bin/python3
# -*- coding: utf-8 -*-

from hermes_python.hermes import Hermes
import random
import os
import json
import requests
import time
import urllib
import sys
from myopenhab import openhab
from myopenhab import mapValues
from myopenhab import getJSONValue

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
        print(self.client_id)
        print(self.client_secret)

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
        
        print("-- Calling Token Service for the first time")

        try:
            r = requests.post(ACCOUNT_URL, data=payload, allow_redirects=False)

            if (self.debug): print(r.headers)
            if (self.debug): print(r.json())
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
            print(" -> Error getting token:" + str(sys.exc_info()[1]))

    def refreshCredentials(self):
        """
        If previous auth token expired, get a new one with refresh token.
        """

        #   Send OAuth payload to get access_token
        payload = { 'refresh_token':self.refresh_token, 'client_id':self.client_id, 'client_secret':self.client_secret, 'redirect_uri':REDIRECT_URI, 'grant_type':'refresh_token' }
        
        print("-- Calling Token Refresh Service")

        try:
            r = requests.post(ACCOUNT_URL, data=payload, allow_redirects=False)

            if (self.debug): print(r.headers)
            if (self.debug): print(r.json())
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
            print(" -> Error refreshing token:" + str(sys.exc_info()[1]))

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
        
        if (time.time() > self.token_expiry):
            self.refreshCredentials()
        headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json" }
        if mode == "POST":
            print("1---------- Post")
            r = requests.post(API_ROOT_URL + path,  headers=headers, data=payload)
            if(r.status_code < 200 and r.status_code > 299):
                print("Response Code = " + str(r.status_code))
                print(r.content)
            return r.status_code
        elif mode == "PUT":
            print("2---------- put")
            r = requests.put(API_ROOT_URL + path,  headers=headers, data=payload)
            if(r.status_code < 200 and r.status_code > 299):
                print("Response Code = " + str(r.status_code))
                print(r.content)
            return r.status_code
        else:
            print("3---------- else ")
            r = requests.get(API_ROOT_URL + path,  headers=headers)
            if(r.status_code < 200 and r.status_code > 299):
                print("Response Code = " + str(r.status_code))
                print(r.content)
            print(r.json())
            return r.json()

    def update(self):
        """
        Get a current player state.
        """
        print("-- Calling Service: Update")
        try:
            resp = self.call("")
            if (self.debug): print(resp)
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

                print(" -> Success")
            else:
                print(" -> Item node missing from response :(")
        except:
            print(" -> Failure: ", sys.exc_info()[0])
            resp = ""

        return resp

    def getDevices(self):
        """
        Get List of Devices
        """
        print("-- Calling Service: Get Devices")
        try:
            resp = self.call("devices")
            resp = json.dumps(resp["devices"])
            self.oh.sendCommand('spotify_device_list',resp)
            if (self.debug): print(resp)
        except:
            print(" -> Device List Failure: ", sys.exc_info()[0])
            resp = ""

        return resp

    def transferPlayback(self):
        """
        Transfer Playback from one device to another
        """
        print("-- Calling Service: Transfer Playback")

        deviceID = self.oh.getState('spotify_current_device_id')

        payload = json.dumps({ 'device_ids': [ deviceID ] })
        print(payload)

        try:
            resp = self.call("","PUT", payload = payload)
            if (self.debug): print(resp)
            self.update()  
        except:
            print(" -> Transfer Playback Failure: ", sys.exc_info()[0])
            resp = ""

        return resp    

    def volumeUp(self):
        """
        Volume up by 10%
        """
        print("-- Calling Service: Volume Up")
        try:
            vol = int(self.oh.getState('spotify_current_volume'))
            vol = int(round(vol/10)*10 + VOL_INCREMENT)
            if(vol>100): 
                vol = 100
            print(" -> Volume To:" + str(vol))
            resp = self.call("volume?volume_percent=" + str(vol),"PUT" )
            self.oh.sendCommand('spotify_current_volume',vol)
            if (self.debug): print(resp)
        except:
            print(" -> VolumeUp Failure: ", sys.exc_info()[0])
            resp = ""

        return resp

    def volumeDown(self):
        """
        Volume down by 10%
        """
        print("-- Calling Service: Volume Down")
        try:
            vol = int(self.oh.getState('spotify_current_volume'))
            vol = int(round(vol/10)*10 - VOL_INCREMENT)
            if(vol<0): 
                vol = 0
            print("Volume To:" + str(vol))
            resp = self.call("volume?volume_percent=" + str(vol),"PUT" )
            self.oh.sendCommand('spotify_current_volume',vol)
            if (self.debug): print(resp)
        except:
            print(" -> VolumeDown Failure: ", sys.exc_info()[0])
            resp = ""

        return resp

    def pause(self):
        """
        Pause player
        """
        print("-- Calling Service: Pause")
        try:
            resp = self.call("pause","PUT")
            self.oh.sendCommand('spotify_current_playing',"OFF")
            if (self.debug): print(resp)
        except:
            print(" -> Pause Failure: ", sys.exc_info()[0])
            resp = ""

        return resp    

    def play(self, context_uri = None):
        """
        Resume player
        """
        print("-- Calling Service: Play")

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
            if (self.debug): print(resp)
            self.update()  
        except:
            print(" -> Play Failure: ", sys.exc_info()[0])
            resp = ""

        return resp        

    def previous(self):
        """
        Skip to previous track
        """
        print("-- Calling Service: Previous")
        try:
            resp = self.call("previous","POST")
            if (self.debug): print(resp)
            self.update()  
        except:
            print(" -> Previous Failure: ", sys.exc_info()[0])
            resp = ""

        return resp        

    def next(self):
        """
        Skip to next track
        """
        print("-- Calling Service: Next")
        try:
            resp = self.call("next","POST")
            if (self.debug): print(resp)
            self.update()
        except:
            print(" -> Next Failure: ", sys.exc_info()[0])
            resp = ""

        return resp

    def updateConnectionDateTime(self):
        self.oh.sendCommand('spotify_lastConnectionDateTime',time.strftime("%Y-%m-%dT%H:%M:%S+0000",time.gmtime(time.time())))     

def action_wrapper(hermes, intent_message):
    os.system("date")
    print("Go message")
    c = spotify()
    item = intent_message.slots.item_random.first().value
    if item == 'coin' or item == 'kopf ' or item == 'münze ':
        coin_random = random.randrange(0, 1)
        if coin_random == 0:
            c.next()
            result_sentence = "Nächstes Lied"
        else:
            c.previous()
            result_sentence = "Lied vorher"
    elif item == 'dice' or item == 'würfel ':
        dice_random = random.randrange(1, 6)
        result_sentence = "Ich habe eine {number} gewürfelt.".format(number=dice_random)
    elif item == 'number' or item == 'zahl ':
        number_random = random.randrange(0, 1000)
        result_sentence = "Die {number} habe ich gerade zufällig gewählt.".format(number=number_random)
    # TODO: random number from range
    else:
        result_sentence = "Diese Funktion ist noch nicht verfügbar."
    current_session_id = intent_message.session_id
    hermes.publish_end_session(current_session_id, result_sentence)


if __name__ == "__main__":
    print("Start")
    with Hermes("localhost:1883") as h:
        h.subscribe_intent("domi:getZufall", action_wrapper).start()
