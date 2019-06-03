#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hermes_python.hermes import Hermes


def action_wrapper(hermes, intent_message):
    first = int(intent_message.slots.firstTerm.first().value)
    second = int(intent_message.slots.secondTerm.first().value)
    if second != 0:
        calc = first / float(second)
        if str(calc)[-2:] == ".0":
            calc = int(calc)
        if "." in str(calc):
            calc_part1, calc_part2 = str(calc).split(".")
            result_sentence = "{0} geteilt durch {1} ergibt {2} komma {3} .".format(first, second,
                                                                                    calc_part1, calc_part2)
        else:
            result_sentence = "{} geteilt durch {} ergibt {} .".format(first, second, calc)
    else:
        result_sentence = "Ich kann leider nicht durch Null teilen."

    current_session_id = intent_message.session_id
    hermes.publish_end_session(current_session_id, result_sentence)


if __name__ == "__main__":
    with Hermes("localhost:1883") as h:
        h.subscribe_intent("domi:getDivision", action_wrapper).start()
