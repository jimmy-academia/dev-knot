import re
import ast
from functools import partial

import logging
from .base import BaseScheme
from tqdm import tqdm

the_script = """
(0)=LLM("Given the following question: {(input)}. Solve the math problem. Please use your knowledge to create a solution by step-by-step manner without any numbers. Every step need to be as easy as possible. Don't use loop or pattern to reduce step. Directly write the numbers from the math problem in the input into the step by step instructions. Clearly write the numbers and the corresponding operations Use Step0, Step1, Step2 to represent result.")
(1)=LLM("{(0)} Output the final integer result, remove all symbols or and explanations, only output the final number.")
        """
class gkNetworkofThought(BaseScheme):
    
    def prep_const_prompt(self):
        self.knowledge_prompt = """
Given the following question:
%s
The Input section is the input query. The Context section is the goal we want to achieve.

Please use your knowledge to create a solution by step-by-step manner without any numbers.
Every step need to be as easy as possible.
Don't use loop or pattern to reduce step.
Directly use the numbers in the input. Clearly write the numbers and the corresponding operations
Use Step0, Step1, Step2 to represent result. The result cannot have any numbers.
"""

        self.script_prompt = """
You have to follow the orders to create a script. script should not contain any numbers.
This script is numbered and contains several orders to be called line-by-line in a sequential order.
Use (index) to represent each line.
index starts from 0.

use LLM("Your Instruction") to find the answer.
Use {(index)} to represent the variable you want to replace with previous result.
Use {(input)}, {(1)}, ... to represent input, not allow to directly use numbers.
Use python indexing to get the element in the list (E.g. {(0)}[0], {(0)}[1]). Do not directly use numbers.

Here is an example:

(0)=LLM("start with _____. Output the number")
(1)=LLM("Operate {(0)} with _____. Output the result")
(2)=LLM("Operate {(1)} with _____. Output the result")
...
(n)=LLM("Clean the output: {(n-1)}. Remove the symbols and only output the integer.")

Based on your expert knowledge

%s

create a script to solve the following question.
"""
        self.system_servent = "You follow orders strictly. Output the answer without any additional information."


    # def llm_answer(self, prompt, planner=False, temperature=0):
    #     model = self.args.planner_llm if planner else self.args.worker_llm
    #     message = [system_struct(self.system_servent), user_struct(prompt)]
    #     return self.llm_call(message, model)

    def prep_task_spcefics(self):
        pass
        # self.tsp_context = Task_Specific_Concept.get(self.args.task)
        # self.tsp_example = Task_Specific_Example.get(self.args.task)

    def solve_query(self, query):
        # goal_prompt = f'Input: {query}\nContext: solve the math problem.'
        # print(goal_prompt)
        
        # knowledge = self.llm_answer(self.knowledge_prompt%goal_prompt, True)
        # print(knowledge)

        # script_prompt = self.script_prompt%knowledge
        # script = self.llm_answer(script_prompt, True)

        script = the_script
        print(script)
        # input('pause')

        cache = {}
        for step in tqdm(script.split('\n'), desc="Processing steps", ncols=90):
            if '=LLM(' not in step:
                continue

            index = re.search(r'\((\d+)\)=LLM', step).group(1)
            instruction = re.search(r'LLM\("(.*?)"\)', step).group(1)

            _sub_with_args = partial(_sub, query=query, cache=cache)
            try:
                instruction = re.sub(r'\{\((\w+)\)\}(?:\[(\d+)\])?', _sub_with_args, instruction)
            except Exception as e:
                print(f"Error during substitution: {e}")
                check()

            print("<<<<<<")
            print(instruction)
            output = self.llm_answer(instruction)
            print(">>>>>>")
            print(output)
            # input()

            try:
                cache[index] = ast.literal_eval(output)
            except:
                cache[index] = output

        print('answer:', self.ground_truth, output, self.ground_truth == output)
        input('finished 1 sample===> pause|')
        return output
    
# def _sub(match, query, cache):
#     var_name = match.group(1)
#     index_str = match.group(2)  # This will be None if no index is specified
    
#     # Determine the base value based on variable name
#     if var_name == 'input':
#         # Handle the input variable specially
#         import ast
#         try:
#             base_value = ast.literal_eval(query)
#         except (SyntaxError, ValueError):
#             # If parsing fails, return the raw query
#             base_value = query
#     else:
#         # For all other variables, get from cache
#         base_value = cache.get(var_name, '')
    
#     # Apply indexing if needed and possible
#     if index_str is not None and isinstance(base_value, (list, tuple)) and base_value:
#         index = int(index_str)
#         if 0 <= index < len(base_value):
#             return base_value[index]
#         else:
#             # Index out of range
#             return ''
    
#     # Return the base value if no indexing or indexing not applicable
#     return base_value


def _sub(match, query, cache):
    var_name = match.group(1)
    index_str = match.group(2)  # This will be None if no index is specified
    
    # Determine the base value based on variable name
    if var_name == 'input':
        # Handle the input variable specially
        import ast
        try:
            base_value = ast.literal_eval(query)
        except (SyntaxError, ValueError):
            # If parsing fails, return the raw query
            base_value = query
    else:
        # For all other variables, get from cache
        base_value = cache.get(var_name, '')
    
    # Apply indexing if needed and possible
    if index_str is not None and isinstance(base_value, (list, tuple)) and base_value:
        index = int(index_str)
        if 0 <= index < len(base_value):
            return str(base_value[index])
        else:
            # Index out of range
            return ''
    
    # Ensure we return a string, even for list types
    if isinstance(base_value, (list, tuple)):
        import json
        return json.dumps(base_value)
    
    # Return the base value as a string
    return str(base_value)