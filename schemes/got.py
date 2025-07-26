import re
import ast
from functools import partial

import logging
from .base import BaseScheme
from debug import *


class GraphofThought(BaseScheme):
    
    def prep_const_prompt(self):
        self.system_servent = "You follow orders strictly. Output the answer without any additional information."

    def prep_task_spcefics(self):
        example = """Input: [REVIEW_1] A menu that satisfies everyone's cravings! Clean, trendy, and delicious! I definitely recommend going early (before 9 am) as the wait tends to get longer after 9 am! But honestly, it is soooo worth the wait. You will leave there feeling so incredible satisfied! [REVIEW_2] I am a long term frequent customer of this establishment. I just went in to order take out (3 apps) and was told they're too busy to do it. Really? The place is maybe half full at best. Does your dick reach your ass? Yes? Go fuck yourself! I'm a frequent customer AND great tipper. Glad that Kanella just opened. NEVER going back to dmitris! Output: 1 Input: [REVIEW_1] The pasta was amazing and the service was excellent! [REVIEW_2] The food was great but the service was terrible. [REVIEW_3] I love this place and will definitely come back. Output: 2"""

        self.script = """(0)=LLM("Split the following batch of review into two: {(input)}. Output an array.")
(1)=LLM("Count how many review in the following batch is Positive: """+example+""" Input {(0)}[0] Output:")
(2)=LLM("Count how many review in the following batch is Positive: """+example+""" Input {(0)}[0] Output:")
(3)=LLM("Combine the two integer counts into a single integer by adding them together. Output only the integer sum. Counts: {(1)} {(2)}. Output")
"""

        # self.context = "Output how many positive reviews in the input. Check every review one by one in the input."

    def solve_query(self, query):

        if self.args.task != 'yelp':
            input("ONLY FOR YELP")
            return False

        cache = {}
        for step in self.script.split('\n'):
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

            # print(instruction)
            output = self.llm_answer(instruction)
            # print(output)
            # input()

            try:
                cache[index] = ast.literal_eval(output)
            except:
                cache[index] = output

        # print('answer:', self.ground_truth, output, self.ground_truth == output)
        # input()
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