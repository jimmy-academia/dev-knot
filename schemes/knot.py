import re
import ast
from functools import partial

import logging
from .base import BaseScheme
from debug import *

Task_Specific_Concept = {
    'addition': "Perform the arithmetic result of input. You can only operate two numbers at a time.",
    'gsm_symbolic': """Solve the question involving different unit measures. Provide the numerical value without any additional string or characters such as % in the final step.)""",
    'game24': "Solve the game of 24. Search for an arithmetic combination of the given four numbers that equates to 24. Arithmetic combination comes in the form of <number><operator><number><operator><number> where <operator> is one of + - * / and <number> is single digit number. You must follow the example to enumerate 6 possible combinations for the first 2 numbers!"
}

Task_Specific_Example = {
    'addition': """example for length = 3 (Script do not contain this line.)
(0)=LLM("Split the sequence {(input)} into a list of numbers. Output a list")
(1)=LLM("Add {(0)}[0] and {(0)}[1]. Only output number.")
(2)=LLM("Add {(1)} and {(0)}[2]. Only output number.")""",
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
    'game24': """
    """
}

"""
    example for the following question: Benny saw a 10-foot shark with 2 6-inch remoras attached to it. What percentage of the shark's body length is the combined length of the remoras? (Script do not contain this line.)
(0)=LLM("Extract the length of the shark and the lengths of the remoras from {(input)}. Output a list in the format [shark_length, remora_length].")
(1)=LLM("Convert the shark length from {(0)}[0] to inches. Output only the numerical value.")
(2)=LLM("Convert the remora length from {(0)}[1] to inches. Output only the numerical value.")
(3)=LLM("Multiply {(2)} by two to find the combined length of the remoras. Output only the numerical value.")
(4)=LLM("Divide {(3)} by {(1)} to calculate the fraction of the shark's length represented by the combined length of the remoras. Output only the numerical value.")
(5)=LLM("Multiply {(4)} by one hundred to convert the result into a percentage. Output only the numerical value.")
"""



class KnowledgeableNetworkofThought(BaseScheme):
    
    def prep_const_prompt(self):
        self.knowledge_prompt = """
Given the following question:
%s
The Input section is the input query. The Context section is the goal we want to achieve.

Please use your knowledge to create a solution by step-by-step manner without any numbers.
Every step need to be as easy as possible.
Don't use loop or pattern to reduce step.
Don't use any numbers in the input. Use first number, second number,....
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
Use {(input)}, {(Set1)}, ... to represent input, not allow to directly use numbers.
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

        print(self.knowledge_prompt%goal_prompt)
        print("============")
        print(knowledge)
        input('knowledge!!')
        
        script_prompt = self.script_prompt%(self.tsp_example, knowledge, goal_prompt)
        # script_prompt = self.script_prompt%(goal_prompt, knowledge, self.tsp_example)
        script = self.llm_answer(script_prompt, True)

        print(script_prompt)
        print("============")
        print(script)

        cache = {}
        for step in script.split('\n'):
            if '=LLM(' not in step:
                continue
            index = re.search(r'\((\d+)\)=LLM', step).group(1)
            instruction = re.search(r'LLM\("(.*?)"\)', step).group(1)
            _sub = partial(_format, cache=cache, query=query)
            try:
                instruction = re.sub(r'\{\((\w+)\)\}(?:\[(\d+)\])?', _sub, instruction)
            except:
                check()

            print("++++")
            print(step)
            print(instruction)
            output = self.llm_answer(instruction)
            print(output)
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


