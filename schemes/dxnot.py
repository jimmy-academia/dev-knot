# for gsm8k

import re
import ast
from functools import partial

from pathlib import Path
import logging

from .base import BaseScheme
from debug import *

import time

# def scale_gsm8k_script(div, context):
#     script = ''
#     div = int(div)
#     for i in range(1,div+1):
#         script += f"""({i})=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")\n"""
#     prev_ans = '"{(' + ')}", "{('.join([str(i) for i in range(1, div+1)])+')}".'
#     script += f"""({div+1})=LLM(" """+context+""" The problem is "{(input)}". You need to carefully check the following five calculation processes and answers, then choose the best final answer: """+prev_ans+""" In the end, extract the numerical value of the final answer you choose and print the value without anything else.")\n"""

#     return script

def scale_gsm8k_script(div, context):
    if div == 5:
        script = """(1)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(2)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(3)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(4)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(5)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(6)=LLM(" """+context+""" The problem is "{(input)}". You need to carefully check the following five calculation processes and answers, then choose the best final answer: "{(1)}", "{(2)}", "{(3)}", "{(4)}", "{(5)}". In the end, extract the numerical value of the final answer you choose and print the value without anything else.")
"""
    elif div == 4:
        script = """(1)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(2)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(3)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(4)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(5)=LLM(" """+context+""" The problem is "{(input)}". You need to carefully check the following four calculation processes and answers, then choose the best final answer: "{(1)}", "{(2)}", "{(3)}", "{(4)}". In the end, extract the numerical value of the final answer you choose and print the value without anything else.")
"""
    elif div == 3:
        script = """(1)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(2)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(3)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(4)=LLM(" """+context+""" The problem is "{(input)}". You need to carefully check the following three calculation processes and answers, then choose the best final answer: "{(1)}", "{(2)}", "{(3)}". In the end, extract the numerical value of the final answer you choose and print the value without anything else.")
"""
    elif div == 2:
        script = """(1)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(2)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(3)=LLM(" """+context+""" The problem is "{(input)}". You need to carefully check the following two calculation processes and answers, then choose the best final answer: "{(1)}", "{(2)}". In the end, extract the numerical value of the final answer you choose and print the value without anything else.")
"""     
    elif div == 1:
        script = """(1)=LLM(" """+context+""" Given the question "{(input)}", list calculation process step-by-step then output the final answer.")
(2)=LLM(" """+context+""" The problem is "{(input)}". You need to carefully check the following calculation processes and answers, then choose the best final answer: "{(1)}". In the end, extract the numerical value of the final answer you choose and print the value without anything else.")
"""     
    return script

def readf(path):
    with open(path, 'r') as f:
        return f.read()

def writef(path, content):
    with open(path, 'w') as f:
        f.write(content)

class dkNetworkofThought(BaseScheme):
    
    def prep_const_prompt(self):
        pass        

    def prep_task_spcefics(self):
        pass

    def solve_query(self, query):
        context = "You are solving a math problem."
        script = scale_gsm8k_script(int(self.args.div), context)
        # print(script)
        # input()

        # print('===')
        # for i in range(1, 6):
        #     print(i)
        #     print(scale_gsm8k_script(i, context))

        # input('===')

        cache = {"input": query}  # Store query directly in cache
        perstep = []
        
        # Parse the script using regex that supports multi-line instructions
        pattern = re.compile(r'\((\d+)\)=LLM\(([\s\n]*)"(.*?)"([\s\n]*)\)', re.DOTALL)
        matches = pattern.finditer(script)
        
        # Process each instruction in numerical order
        instructions = [(int(match.group(1)), match.group(3)) for match in matches]
        instructions.sort()  # Sort by index
        
        for idx, instruction_text in instructions:
            idx_str = str(idx)
            
            # Replace variable references with their values
            try:
                formatted_instruction = re.sub(
                    r'\{\((\w+)\)\}(?:\[(\d+)\])?', 
                    lambda m: _format(m, cache, query), 
                    instruction_text
                )
            except Exception as e:
                print(f"Error formatting instruction {idx}: {e}")
                check()

            # print(f">>> original: <<<\n{instruction_text}")
            # print(f">>> formatted: <<<\n{formatted_instruction}")

            # Execute the instruction
            start = time.time()
            output = self.llm_answer(formatted_instruction)
            duration = time.time() - start
            perstep.append(duration)
            
            # print(f'>>> output: <<<\n{output}')
            # input()


            # Handle RETURN directive
            if "RETURN" in output:
                return output.replace("RETURN", "").strip()
            
            # Store the result
            try:
                cache[idx_str] = ast.literal_eval(output)
            except (SyntaxError, ValueError):
                cache[idx_str] = output

        self.perstep_runtimes.extend(perstep)
        self.total_runtimes.append(sum(perstep))

        # Get final result
        if instructions:
            last_idx = str(instructions[-1][0])
            final_output = cache.get(last_idx, "")
            # logging.info(f'>>>>>>>>>>>> query: {query} <<<<<<<<<<<<<')
            # logging.info(f'>>>>>>>>>>>> final result: {final_output} <<<<<<<<<<<<<')
            # print(self.ground_truth)
            # input()
            return final_output
        

        return "No output generated"

def _format(match, cache, query):
    key = match.group(1)
    index = match.group(2)
    if key == "input":
        return query
    elif index:
        return str(cache[key][int(index)])
    else:
        return str(cache[key])


# o3-mini-high
    