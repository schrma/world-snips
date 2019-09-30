
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


def action_next(hermes, intent_message):
    print("Spotify next")
    result_sentence = "Nächstes Lied"
    current_session_id = intent_message.session_id
    hermes.publish_end_session(current_session_id, result_sentence)


def action_play(hermes, intent_message):
    print("Spotify play")
    result_sentence = "Starte Lied"
    current_session_id = intent_message.session_id
    hermes.publish_end_session(current_session_id, result_sentence)


def action_previous(hermes, intent_message):
    print("Spotify previous")
    result_sentence = "Vorheriges Lied"
    current_session_id = intent_message.session_id
    hermes.publish_end_session(current_session_id, result_sentence)


def action_pause(hermes, intent_message):
    print("Spotify pause")
    result_sentence = "Mache mal eine Pause"
    current_session_id = intent_message.session_id
    hermes.publish_end_session(current_session_id, result_sentence)


if __name__ == "__main__":
    print("Start Spotify")
    with Hermes("localhost:1883") as h:
        h.subscribe_intent("schrma:previous", action_previous)
        h.subscribe_intent("schrma:next", action_next)
        h.subscribe_intent("schrma:play", action_play)
        h.subscribe_intent("schrma:pause", action_pause)
        h.loop_forever()
