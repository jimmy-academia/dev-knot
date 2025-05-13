import re
import ast
from functools import partial

from pathlib import Path
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

def readf(path):
    with open(path, 'r') as f:
        return f.read()

def writef(path, content):
    with open(path, 'w') as f:
        f.write(content)

class rkNetworkofThought(BaseScheme):
    
    def prep_const_prompt(self):
        self.knowledge_prompt = """
Given the following question:
%s

And a solution structure example for four numbers:
%s

Please use your knowledge to create a solution structure for five numbers
CAREFULLY CHECK EVERYSTEP. MAKE SURE IT HAS THE INPUT FIELD {(N)} IT NEEDS TO REFERENCE OUTPUT FROM A PREVIOUS STEP. Make sure it is in the correct syntax. E.g., (from (0)) should be {(0)}!!! MAKE SURE EACH STEP REFERENCES THE CORRESPONDING STEP, FOLLOWING THE SOLUTION STRUCTURE FOR FOUR NUMBERS. MAKE SURE THE EXAMPLE IN THE INSTRUCTION ARE UPDATED FROM FOUR NUMBER TO FIVE NUMBER CASE, I.E. ADD ONE MORE NUMBER TO THE EXAMPLE, e.g., [2 \times 3 4 8 | 6 4 8] becomes [2 \times 3 4 8 1 | 6 4 8 1]
"""

        self.script_prompt = """
You have to create a script to solve Game of 24 for five numbers.
Context:
%s

The script should be numbered and contains several orders to be called line-by-line in a sequential order.
Use (index) to represent each line.
index starts from 0.

You can use LLM Inference: use LLM("Your Instruction") to find the answer.
Here is one example script for four numbers.
%s

Use {(index)} to represent the variable you want to replace with previous result.
Use {(input)}, {(1)}, ... to represent input, not allow to directly use numbers.
Use python indexing to get the element in the list (E.g. {(0)}[0], {(0)}[1]).
Follow the syntax of the example script.

Use your knowledge in the following:

%s

Parse the knowledge;
CAREFULLY CHECK EVERYSTEP. MAKE SURE IT HAS THE INPUT FIELD {(N)} IT NEEDS TO REFERENCE OUTPUT FROM A PREVIOUS STEP. Make sure it is in the correct syntax. E.g., (from (0)) should be {(0)}!!!
Output only the final script.

"""
            
        cache_script = Path(f'cache/script_5rknot-o3-mini-high')
        # cache_knowledge = Path(f'cache/knowledge_5rknot-{self.args.planner_llm}')

        if cache_script.exists():
            logging.info(f'loading {cache_script}')
            self.script = readf(cache_script)

        else:
            prompt = self.knowledge_prompt%(context, script)
            print('=======')
            print(prompt)
            print('=======')
            input()
            # knowledge = self.llm_answer(prompt, True)

            knowledge = readf('cache/knowedge_5rknot-o3-mini-high')

            prompt = self.script_prompt%(context, script, knowledge)
            print('=======')
            print(prompt)
            print('=======')
            input()
            self.script = readf('cache/script_5rknot-o1')

        # print(self.script)


    def prep_task_spcefics(self):
        pass

    def solve_query(self, query):
        
        script = self.script

        cache = {"input": query}  # Store query directly in cache
        
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

            print(f">>> original: <<<\n{instruction_text}")
            print(f">>> formatted: <<<\n{formatted_instruction}")

            # Execute the instruction
            output = self.llm_answer(formatted_instruction, temperature=0.7)
            print(f'>>> output: <<<\n{output}')
            # input()


            # Handle RETURN directive
            if "RETURN" in output:
                return output.replace("RETURN", "").strip()
            
            # Store the result
            try:
                cache[idx_str] = ast.literal_eval(output)
            except (SyntaxError, ValueError):
                cache[idx_str] = output

        # Get final result
        if instructions:
            last_idx = str(instructions[-1][0])
            final_output = cache.get(last_idx, "")
            logging.info(f'>>>>>>>>>>>> query: {query} <<<<<<<<<<<<<')
            logging.info(f'>>>>>>>>>>>> final result: {final_output} <<<<<<<<<<<<<')
            # input()
            return final_output
        
        return "No output generated"

    def dep_solve_query(self, query):

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
        input('pause')
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


# o3-mini-high