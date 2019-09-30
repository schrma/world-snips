
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
from spotify import spotify
from myopenhab import openhab
from myopenhab import mapValues
from myopenhab import getJSONValue


def action_wrapper(hermes, intent_message):
    os.system("date")
    print("Go message")
    c = spotify()
    item = intent_message.slots.item_random.first().value
    if item == 'coin' or item == 'kopf ' or item == 'münze ':
        c.next()
        result_sentence = "Nächstes Lied"
    elif item == 'dice' or item == 'würfel ':
        c.previous()
        result_sentence = "Lied vorher"
    elif item == 'number' or item == 'zahl ':
        c.pause()
        result_sentence = "Mach mal eine Pause"
    else:
        result_sentence = "Diese Funktion ist noch nicht verfügbar."
    current_session_id = intent_message.session_id
    hermes.publish_end_session(current_session_id, result_sentence)


if __name__ == "__main__":
    print("Start")
    with Hermes("localhost:1883") as h:
        h.subscribe_intent("domi:getZufall", action_wrapper).start()
