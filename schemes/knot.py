import re
import ast
from functools import partial

import logging
from .base import BaseScheme
from debug import *
from utils import _sub

Task_Specific_Concept = {
    'yelp': "Output how many positive reviews in the input. Check every review one by one in the input.",
    'keyword': "Output all words about countries in the article. You can seperate article into sentences first. The maximum number of sentences is 20.",
    'sorting': "Sort input in ascending order. You can use counting sort.",
    'intersection': "Find the intersection of two input. You can check every element in set1 one by one.",
    'arithmetic': """Perform the arithmetic result of input. 
You can only operate two numbers at a time. Calculate from left to right. Do multiplication and division first.""",
    'large_digit': "Calculate the result of the input. You can plus one digit from one digit strating from the least significant digit.",
    'add_mul': """Perform the arithmetic result of input. 
You can only operate two numbers at a time. Calculate from left to right. Do multiplication and division first.""",    
    'addition': "Perform the arithmetic result of input. You can only operate two numbers at a time.",
    'gsm_symbolic': """Solve the question involving different unit measures. Provide the numerical value without any additional string or characters such as % in the final step.)""",
}

Task_Specific_Example = {
    'yelp': """
```example for length = 10
(0)=LLM("Check the following review is Positive or Negative: {(input)}[0].")
(1)=LLM("Check the following review is Positive or Negative: {(input)}[1].")
(2)=LLM("Check the following review is Positive or Negative: {(input)}[2].")
...
(9)=LLM("Check the following review is Positive or Negative: {(input)}[length-1].")
(10)=LLM("[{(0)}, {(1)}, {(2)}, {(3)}, {(4)}, {(5)},.... ,{(length-1)}], output the number of Positive.")""",
    'keyword': """
```example length = 20
(0)=LLM("Split the following article into sentences: '{(input)}'. Output an array.")
(1)=LLM("Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[0]"  Output [] if not exist any country.")
(2)=LLM("Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[1]"  Output [] if not exist any country.")
(3)=LLM("Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[2]"  Output [] if not exist any country.")
...
(20)=LLM("Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[19]"  Output [] if not exist any country.")
(21)=LLM("Combine {(1)}, {(2)}, {(3)}, {(4)}, {(5)}, {(6)}, {(7)}, {(8)}, {(9)}, {(10)}, {(11)}, {(12)}, {(13)}, {(14)}, {(15)}, {(16)}, {(17)}, {(18)}, {(19)}, {(20)} in one array. Repeated is allowed.")""",
    'sorting': """
```example for length = 32 (Script do not contain this line.)
(0)=LLM("Initialize an array of size 10 to zero.")
(1)=LLM("Increment the count at index {(input)}[0] in {(0)} (index start from 0). Only output updated array.")
(2)=LLM("Increment the count at index {(input)}[1] in {(1)} (index start from 0). Only output updated array.")
...
(16)=LLM("Increment the count at index {(input)}[15] (start from 0) in {(15)}. Only output updated array.")
...
(length+1)=LLM("Convert {(length)} in English. Output an array.")
(length+2)=LLM("The array should contain {(length+1)}[0] 0s, {(length+1)}[1] 1s, {(length+1)}[2] 2s, {(length+1)}[3] 3s, {(length+1)}[4] 4s. Output in array format.")
(length+3)=LLM("The array should contain {(length+1)}[5] 5s, {(length+1)}[6] 6s, {(length+1)}[7] 7s, {(length+1)}[8] 8s, {(length+1)}[9] 9s. Output in array format.")
(length+4)=LLM("Combine {(length+2)} and {(length+3)} in ascending order. Only output array.")""",
    'intersection':"""
```example for length = 128 (Script do not contain this line.)
(0)=LLM("Find the intersection for [{(Set1)}[0]] and {(Set2)}. Output [] if mutually exclusive.")
(1)=LLM("Find the intersection for [{(Set1)}[1]] and {(Set2)}. Output [] if mutually exclusive.")
...
(length-1)=LLM("Find the intersection for [{(Set1)}[length-1]] and {(Set2)}. Output [] if mutually exclusive.")
(length)=LLM("Combine {(0)}, {(1)}, {(2)},  ... ,{(length-1)} in one array.")""",
    'addition': """example for length = 3 (Script do not contain this line.)
(0)=LLM("Split the sequence {(input)} into a list of numbers. Output a list")
(1)=LLM("Add {(0)}[0] and {(0)}[1]. Only output number.")
(2)=LLM("Add {(1)} and {(0)}[2]. Only output number.")""",
    'arithmetic': """
```example for some basic operation
(0)=LLM("Given {(input)}, Split the numbers without operators. Only output list.")
(1)=LLM("Add({(0)}[0], {(0)}[2]). Only output number. If contains floating point, round to two decimal places.")
(2)=LLM("Subtraction({(0)}[1], {(1)}). Only output number. If contains floating point, round to two decimal places.")
(3)=LLM("Multiply({(0)}[1], {(1)}). Only output number. If contains floating point, round to two decimal places.")
(4)=LLM("Divide({(0)}[1], {(1)}). Only output number. If contains floating point, round to two decimal places.")""",
    'large_digit':"""
```example for length = 32
(0)=LLM("Split "{(input)}" by + and output in string format in an array.")
(1)=LLM("Calculate {(0)}[0][15]+{(0)}[1][15]. Only output result.")
(2)=LLM("Calculate {(1)} divide 10, Only output integer.")
(3)=LLM("Calculate {(2)}+{(0)}[0][14]+{(0)}[1][14]. Only output result.")
(4)=LLM("Calculate {(3)} divide 10, Only output integer.")
(5)=LLM("Calculate {(4)}+{(0)}[0][13]+{(0)}[1][13]. Only output result.")
(6)=LLM("Calculate {(5)} divide 10, Only output integer.")
......
(2*length-1)=LLM("Calculate {(2*length-2)}+{(0)}[0][0]+{(0)}[1][0]. Only output result.")
(2*length)=LLM("Calculate {(2*length-1)} divide 10, Only output integer.")
(2*length+1)=LLM("Convert into an integer: {(2*length)}{(2*length-1)}[-1]{(2*length-3)}[-1]{(2*length-5)}[-1]......{(25)}[-1]{(23)}[-1]{(21)}[-1]{(19)}[-1]{(17)}[-1]{(15)}[-1]{(13)}[-1]{(11)}[-1]{(9)}[-1]{(7)}[-1]{(5)}[-1]{(3)}[-1]{(1)}[-1]")""",
    'gsm_symbolic': 
"""
Input: There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today? (Script do not contain this line.)
Example:
    (0)=LLM("Extract the initial number of trees and the total number of trees after planting from {(input)}. Output a list in the format [initial_trees, total_trees].")
    (1)=LLM("Subtract the initial number of trees {(0)}[0] from the total number of trees {(0)}[1]. Output only the numerical value.")
    (2)=LLM("The result from {(1)} is the number of trees planted by the grove workers. Output the  number.")

Input: If there are 3 cars in the parking lot and 2 more cars arrive, how many
      cars are in the parking lot?
Example:
    (0)=LLM("Extract the initial number of cars and the subsequent number of cars from the input query: {(input)}. Output a list in the format [initial_cars, subsequent_cars].")
    (1)=LLM("{(0)}[0]+{(0)}[1]. Output only the numerical value.")
    """,
}

class KnowledgeableNetworkofThought(BaseScheme):
    
    def prep_const_prompt(self):
        self.knowledge_prompt = """
Given the following question:
%s
The Input section is the input query. The Context section is the goal we want to achieve.

Please use your knowledge to create a solution by step-by-step manner without any numbers.
Every step need to be as easy as possible.
Don't use loop or pattern to reduce step.
Don't use any numbers/sentence in the input. Use first number/sentence, second number/sentence,....
Use Step0, Step1, Step2 to represent result. The result cannot have any numbers.
"""

#         = '''
# Please use your knowledge to create a solution in a  step-by-step manner.
# Every step need to be as easy as possible.
# Don't use loop or pattern to reduce step.
# Don't copy any numbers or words from the input. Refer to the positions, such as first number, second number,....'''

        self.script_prompt = """
You have to follow the orders to create a script. script should not contain any numbers.
This script is numbered and contains several orders to be called line-by-line in a sequential order.
Use (index) to represent each line.
index starts from 0.

You can use LLM Inference: use LLM("Your Instruction") to find the answer.
Here is one example.
%s

Use {(index)} to represent the variable you want to replace with previous result.
Use {(input)}, {(1)}, ... to represent input, not allow to directly use numbers.
Use python indexing to get the element in the list (E.g. {(0)}[0], {(0)}[1]).
Do not directly use numbers.

Based on your expert knowledge \n %s and the above example, create a script to solve the following question:
%s
The Input section is the input query. The Context section is the goal we want to achieve.
"""

#         = '''
# Create a script which contains several instructions to be called line-by-line by an LLM in a sequential order.
# Each line is (index)=LLM("Your instruction")
# Use (index) to label each instruction; index starts from 0.
# Use {(index)} to represent the output from a previous result.
# Use python indexing to get the element in the list (E.g. {(0)}[0], {(0)}[1]).
# Don't copy any numbers or words from the input. Refer to the positions.

# EXAMPLE:
# %s

# Based on your expert knowledge %s and the above example, create a script to solve the following question:
# %s
# The Input section is the input query. 
# The Context section is the goal we want to achieve.
# '''


    def prep_task_spcefics(self):
        self.tsp_context = Task_Specific_Concept.get(self.args.task)
        self.tsp_example = Task_Specific_Example.get(self.args.task)

    def solve_query(self, query):
        goal_prompt = f'Input: {query}\nContext: {self.tsp_context}'
        knowledge = self.llm_answer(self.knowledge_prompt%goal_prompt, True)

        # print(self.knowledge_prompt%goal_prompt)
        # print("============")
        # print(knowledge)
        # input('knowledge!!')
        
        script_prompt = self.script_prompt%(self.tsp_example, knowledge, goal_prompt)
        # script_prompt = self.script_prompt%(goal_prompt, knowledge, self.tsp_example)
        script = self.llm_answer(script_prompt, True)

        # print(script_prompt)
        # print("============")
        # print(script)

        cache = {}
        for step in script.split('\n'):
            if '=LLM(' not in step:
                continue

            index = re.search(r'\((\d+)\)=LLM', step).group(1)
            instruction = re.search(r'LLM\("(.*?)"\)', step).group(1)

            _sub_with_args = partial(_sub, query=query, cache=cache)
            try:
                instruction = re.sub(r'\{\((\w+)\)\}(?:\[(\d+)\])?', _sub_with_args, instruction)
            except Exception as e:
                print(f"Error during substitution: {e}")

            # print("++++")
            # print(step)
            # print(instruction)
            output = self.llm_answer(instruction)
            # print(output)
            # input()

            if "RETURN" in output:
                output = output.replace("RETURN", "").strip()
                return output
            # input('>>> step by step pause and check')
            try:
                cache[index] = ast.literal_eval(output)
            except:
                cache[index] = output

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


