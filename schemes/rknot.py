import re
import ast
from functools import partial

import logging
from .base import BaseScheme
from debug import *

def readf(path):
    with open(path, 'r') as f:
        return f.read()

def writef(path, content):
    with open(path, 'w') as f:
        f.write(content)


class RKnowledgeableNetworkofThought(BaseScheme):
    
    def prep_const_prompt(self):
        self.script = """(0)=LLM("You are solving for Game of 24. You need to use an arithmetic expression with 4 numbers to form 24. Each step you can only connect 2 numbers. Given {(input)} what is the most possible next step?")
        (1)=LLM("Partial solution to Game of 24 contains unfinished arithmetic expressions for 4 numbers. Examples of partial solutions `2*3 4 8` `1 4+5 7` `3 4 3*4`. {(0)} Follow the step to give a partial solution for {(input)}. Only output the partial solution.")
        (2)=LLM("You are solving for game of 24. You need to use an arithmetic expression with 4 numbers to form 24. Each step you can only connect 2 numbers. Given {(1)} what is the most possible next step?")
        (3)=LLM("Partial solution to Game of 24 contains unfinished arithmetic expressions for 4 numbers. Examples of partial solutions `2*3 4+8` `1*4+5 7` `3*4 3*4`. {(2)} Follow the step to give a partial solution for {(input)}. Only output the partial solution.")
        """

    def prep_task_spcefics(self):
        pass

    def solve_query(self, query):
        script = self.script

        cache = {}
        for step in script.split('\n'):
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
            print("formatted:")
            print(instruction)
            output = self.llm_answer(instruction)
            print('output')
            print(output)
            input()

            if "RETURN" in output:
                output = output.replace("RETURN", "").strip()
                return output
            # input('>>> step by step pause and check')
            try:
                cache[index] = ast.literal_eval(output)
            except:
                cache[index] = output

        logging.info(f'>>>>>>>>>>>> final result: {output} <<<<<<<<<<<<<')
        input('pause!!!')
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


