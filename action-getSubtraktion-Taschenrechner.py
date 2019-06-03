#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hermes_python.hermes import Hermes


def action_wrapper(hermes, intent_message):
    first = int(intent_message.slots.firstTerm.first().value)
    second = int(intent_message.slots.secondTerm.first().value)
    calc = first - second
    if str(calc)[-2:] == ".0":
        calc = int(calc)
    result_sentence = "{} minus {} ergibt {} .".format(first, second, calc)
    current_session_id = intent_message.session_id
    hermes.publish_end_session(current_session_id, result_sentence)


if __name__ == "__main__":
    with Hermes("localhost:1883") as h:
        h.subscribe_intent("domi:getSubtraktion", action_wrapper).start()
