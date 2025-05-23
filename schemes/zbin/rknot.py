import re
import ast
from functools import partial

import logging
from .base import BaseScheme
from debug import *

context = "You are solving for Game of 24. You need to carefully design an arithmetic expression with all the numbers given to you to form 24. You must use each numbers exactly once. You may use + - \\times and parenthesis. You need to carefully design an arithmetic expression using EACH NUMBERS EXACTLY ONCE. Hint: 24 can be obtained by 1 \\times 24, 2 \\times 12, 3 \\times 8, 4 \\times 6 or 1+23, 2+22, 3+21, 4+20, 5+19, 6+18, 7+17, 8+16, 9+15, 10+14, 11+14, 12+12. Hint: 1 mulitplied to anything keeps it unchanged! 1\\times 24=24, 1\\times 4=4, 1\\times 6=6, 1\\times 1=1. YOU CAN ONLY USE THE NUMBERS GIVEN TO YOU and NOTHING ELSE. Thus, you should think carefully whether the remaining numbers can form the other value needed to reach 24. Each step you can only connect 2 numbers. "

script = """(0)=LLM(" """+context+""" Given {(input)}, what is the most possible next step? Give me 12 most likely options that combines two of the numbers arithmetically using addition, subtraction, multiplication.")
(1)=LLM(" """+context+""" Given {(input)}, what is the most possible next step? Here are 12 options that combines two of the numbers arithmetically using addition, subtraction, multiplication. {(0)} Analyze each option and consider whether the remaining three values may be combined arithmetically to obtain 24.")
(2)=LLM(" """+context+""" The numbers are {(input)}. {(1)} Conduct the step and obtain the partial solution. Ouput the current state after taking the step as [arithmetic expression | three remaining values], such as [2 \\times 3 4 8 | 6 4 8]. Only output the state and nothing else.")
(3)=LLM("{(2)} Output the three values on the right hand side of the squre bracket.")
(4)=LLM(" """+context+""" Given {(3)}, what is the most possible next step? Give me 12 most likely options that combines two of the numbers arithmetically using addition, subtraction, multiplication."")
(5)=LLM(" """+context+""" Given {(3)}, what is the most possible next step? Here are 12 options that combines two of the numbers arithmetically using addition, subtraction, multiplication. {(4)} Analyze each option and consider whether the remaining two values may be combined arithmetically to obtain 24. DO NOT USE ANY VALUE BESIDES THE THREE VALUES IN {(3)}. Give me your reasoning:")
(6)=LLM(" """+context+""" Given {(3)}, what is the most possible next step? Here are 12 options that combines two of the numbers arithmetically using addition, subtraction, multiplication. {(4)} Here is a reasoning analysis {(5)}.")
(7)=LLM(" """+context+""" The numbers are {(3)}. {(6)} Conduct the step and obtain the partial solution. Ouput the current state after taking the step as [arithmetic expression | two remaining values], such as [1 \\times 6 4 | 6 4]. Only output the state and nothing else.")
(8)=LLM("{(7)} Output the two values on the right hand side of the squre bracket.")
(9)=LLM(" """+context+""" The numbers are {(8)}. How to obtain 24?")
(10)=LLM("{(2)} Output the arithmetic expression on the left hand side of the squre bracket.")
(11)=LLM("{(7)} Output the arithmetic expression on the left hand side of the squre bracket.")
(12)=LLM(" """+context+""" Given {(input)}, we have taken these steps: Step 1: {(10)}; Step 2: {(11)}; Step 3: {(9)}. What is the correct arithmetic expression that obtains 24?")
"""

class RKnowledgeableNetworkofThought(BaseScheme):
    
    def prep_const_prompt(self):
        self.script = script

    def prep_task_spcefics(self):
        pass

    def solve_query(self, query):
        cache = {}
        for step in self.script.split('\n'):
            if '=LLM(' not in step:
                continue

            step = step.strip()
            index = re.search(r'\((\d+)\)=LLM', step).group(1)
            instruction = re.search(r'LLM\("(.*?)"\)', step).group(1)
            _sub = partial(_format, cache=cache, query=query)
            try:
                instruction = re.sub(r'\{\((\w+)\)\}(?:\[(\d+)\])?', _sub, instruction)
            except:
                check()

            print("++++")
            print(step)
            print(">>> formatted: <<<")
            print(instruction)
            output = self.llm_answer(instruction, temperature=0.7)
            print('output')
            print(output)

            if "RETURN" in output:
                output = output.replace("RETURN", "").strip()
                return output
            # input('>>> step by step pause and check')
            try:
                cache[index] = ast.literal_eval(output)
            except:
                cache[index] = output

        logging.info(f'>>>>>>>>>>>> query: {query} <<<<<<<<<<<<<')
        logging.info(f'>>>>>>>>>>>> final result: {output} <<<<<<<<<<<<<')

        return output
    
def _format(match, cache, query):
    key = match.group(1)
    index = match.group(2)
    if key == "input":
        return query
    elif index:
        return str(cache[key][int(index)])
    else:
        return str(cache[key])


