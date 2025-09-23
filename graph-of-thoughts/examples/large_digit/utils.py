# Copyright (c) 2023 ETH Zurich.
#                    All rights reserved.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# main author: Nils Blach

from typing import Dict, List
import logging
import re
import json
import argparse

def string_to_list(string: str) -> List[int]:
    """
    Helper function to convert a list encoded inside a string into a Python
    list object of string elements.

    :param string: Input string containing a list.
    :type string: str
    :return: List of string elements.
    :rtype: List[str]
    :raise AssertionError: If input string does not contain a list.
    """

    # assert string[0] == "[" and string[-1] == "]", "String is not a list."
    return [int(num) for num in string[1:-1].split(",")]


def test_sorting(state: Dict) -> bool:
    """
    Function to test whether the final solution matches ground truth.

    :param state: Thought state that represents the final solution.
    :type state: Dict
    :return: Returns whether the solution matches the ground truth.
    :rtype: bool
    """

    try:
        correct_answer = eval(state["original"])
        cal_answer = int(state["current"][0] if type(state["current"]) == type([]) else state["current"])
        print("correct_answer: ", correct_answer)
        print("cal_answer    : ", cal_answer)
        print("matches ground truth: ", correct_answer == cal_answer)
        print("----------------------------")
        return correct_answer == cal_answer
    except:
        return False


def num_errors(state: Dict) -> float:
    """
    Function to locally count the number of errors that serves as a score.

    :param state: Thought state to be scored.
    :type state: Dict
    :return: Number of errors.
    :rtype: float
    """

    # correct_answer = eval(state["original"])
    try: 
        logging.info(f"{state}")
        
        cal_answer = state["current"]
        if type(cal_answer) == type([]):
            cal_answer = cal_answer[0]
        cal_answer = float(cal_answer)

        correct_answer = eval(state["uncalculated_seq"])


        num_errors = abs(correct_answer-cal_answer)
        return num_errors
    except:
        return 1145141919
    

class NamespaceEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, argparse.Namespace):
      return obj.__dict__
    else:
      return super().default(obj)

def dumpj(dictionary, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        obj = json.dumps(dictionary, indent=4, cls=NamespaceEncoder, ensure_ascii=False)
        obj = re.sub(r'("|\d+),\s+', r'\1, ', obj)
        obj = re.sub(r'\[\n\s*("|\d+)', r'[\1', obj)
        obj = re.sub(r'("|\d+)\n\s*\]', r'\1]', obj)
        f.write(obj)