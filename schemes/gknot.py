import re
import ast
import json
from functools import partial
from tqdm import tqdm
import logging

from .base import BaseScheme

Task_Specific_Concept = {
    'gsm8k': "Solve the final problem to find the sum of the answer to each problems. Solve the problems one by one, then add the answers together.",
    # (other tasks omitted for brevity)
}

Task_Specific_Example = {
    'gsm8k': """example for length = 2
(0)=LLM(\"Split the following problem batch into a list of individual problems. Output a JSON list like this: [\"Problem 0...\", \"Problem 1...\", ...]. Do NOT include any explanation or additional text. Input: {(input)}\")
(1)=LLM(\"{(0)}[0] Let's think step by step. Becareful to clarify the concepts and how to form the formula. Give me your reasoning and the final answer.\")
(2)=LLM(\"extract the numerical from the answer: {(1)}\")
(3)=LLM(\"{(0)}[1] Let's think step by step. Becareful to clarify the concepts and how to form the formula. Give me your reasoning and the final answer.\")
(4)=LLM(\"extract the numerical from the answer: {(3)}\")
(5)=LLM(\"Add {(2)} and {(4)}. Only output the number and arrive at the answer.\")""",
    # (other examples omitted)
}

class gkNetworkofThought(BaseScheme):

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

        self.script_prompt = """
You have to follow the orders to create a script. script should not contain any numbers.
This script is numbered and contains several orders to be called line-by-line in a sequential order.
Use (index) to represent each line.
index starts from 0.

You can use LLM Inference: use LLM(\"Your Instruction\") to find the answer.
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

        self.system_servent = "You follow orders strictly. Output the answer without any additional information."

    def prep_task_spcefics(self):
        self.tsp_context = Task_Specific_Concept.get(self.args.task)
        self.tsp_example = Task_Specific_Example.get(self.args.task)

    def solve_query(self, query):
        goal_prompt = f'Input: {query}\nContext: {self.tsp_context}'
        print(goal_prompt)

        knowledge = self.llm_answer(self.knowledge_prompt % goal_prompt, True)
        print(knowledge)

        script_prompt = self.script_prompt % (self.tsp_example, knowledge, goal_prompt)
        script = self.llm_answer(script_prompt, True)
        print(script)

        cache = {}
        for step in tqdm(script.split('\n'), desc="Processing steps", ncols=90):
            if '=LLM(' not in step:
                continue

            index = re.search(r'\((\d+)\)=LLM', step).group(1)
            match = re.search(r'LLM\((?P<quote>[\"\'])(.*?)\1\)', step)
            instruction = match.group(2)

            _sub_with_args = partial(_sub, query=query, cache=cache)
            try:
                instruction = re.sub(r'\{\((\w+)\)\}(?:\[(\d+)\])?', _sub_with_args, instruction)
            except Exception as e:
                print(f"Error during substitution: {e}")
                continue

            print("<<<<<<")
            print(instruction)
            output = self.llm_answer(instruction)
            print(">>>>>>")
            print(output)
            # input()

            try:
                if output.strip().startswith("[") and output.strip().endswith("]"):
                    cache[index] = json.loads(output)
                else:
                    cache[index] = ast.literal_eval(output)
            except Exception as e:
                print(f"Parsing failed at step {index}: {e}")
                cache[index] = output

        print('answer:', self.ground_truth, output, self.ground_truth == output)
        input('finished 1 sample===> pause|')
        return output

def _sub(match, query, cache):
    var_name = match.group(1)
    index_str = match.group(2)

    if var_name == 'input':
        try:
            base_value = ast.literal_eval(query)
        except:
            base_value = query
    else:
        base_value = cache.get(var_name, '')

    if index_str is not None and isinstance(base_value, (list, tuple)):
        index = int(index_str)
        try:
            return str(base_value[index])
        except IndexError:
            print(f"[Warning] Index {index} out of range for variable {var_name} with value: {base_value}")
            return ''

    if isinstance(base_value, (list, tuple)):
        return json.dumps(base_value)

    return str(base_value)
