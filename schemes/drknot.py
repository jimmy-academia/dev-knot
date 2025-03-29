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

game24context="Solve the game of 24. You are given four numbers. Use numbers and basic arithmetic operations + - * / and parenthesis  to obtain 24. First, you can use the syntax representation [\"1+2 5 6 | 3 3 4\"] to represent partial solutions and the remaining numerical values. Next, you should take several steps, where in each step, you are only allowed to choose two of the remaining numbers to obtain a new number. In particular, you can conduct LLM actions to propose several next steps each syntax representation received in the current step. After each step, you should also organize them into a flat list, evaluate each result, and select the top candidates for next step. Finally, evaluate each equation and return the first one that correctly equates to 24."


propose_prompt = '''Use numbers and basic arithmetic operations + - * / and parenthesis  to obtain 24. /) to obtain 24. Each step, you are only allowed to choose two of the remaining numbers to obtain a new number.
Input: [" 4 6 12 | 4 6 12 "]
Possible next step: [" 6-4 12 | 2 12 "]
Input: [" 9 10 24 | 9 10 24 "]
Possible next step: [" 10-9 24 | 1 24 "]
Input: [" 3 4 9 | 3 4 9 "]
Possible next step: [" 9-3 4 | 6 4 "]
Input: [" 1 2 8 | 1 2 8 "]
Possible next steps: [" 1+2 8 | 3 8 "]
Input: [" 5 9 10 | 5 9 10 "]
Possible next steps: [" 5+10 9 | 15 9 "]; [" 5+9 10 | 14 10 "]; [" 9+10 5 | 19 5 "]
Input: [" 1 4 6 | 1 4 6 "]
Possible next steps: [" 1*4 6 | 4 6 "]; [" 1*6 4 | 6 4 "]; [" 4*6 1 | 24 1 "]
Input: [" 4 8 12 | 4 8 12 "]
Possible next steps: [" 8/4 12 | 2 12 "]; [" 4+8 12 | 12 12 "]; [" 12/4 8 | 3 8 "]
Input: {(item)}
Possible next steps:
'''

propose_prompt2 = '''Use numbers and basic arithmetic operations + - * / and parenthesis  to obtain 24. /) to obtain 24. Each step, you are only allowed to choose two of the remaining numbers to obtain a new number.
Input: [" 6-4 12 | 2 12 "]
Possible next step: [" (6-4)*12 | 24 "]
Input: [" 10-9 24 | 1 24 "]
Possible next step: [" (10-9)*24 | 24 "]
Input: [" 9-3 4 | 6 4 "]
Possible next step: [" (9-3)*4 | 24 "]
Input: [" 5+10 9 | 15 9 "]
Possible next steps: [" 5+10+9 | 24 "]
Input: [" 12/4 8 | 3 8 "]
Possible next steps: [" 12/4*8 | 24 "]
Input: {(item)}
Possible next steps:
'''

evaluate_prompt = '''Evaluate if given state can reach 24 (sure/likely/impossible)
[" 2*5 14 | 10 14 "]
10 + 14 = 24
sure
[" 4+7 12 | 11 12 "]
11 + 12 = 23
12 - 11 = 1
11 * 12 = 132
11 / 12 = 0.91
impossible
[" 4 4 10 | 4 4 10 "]
4 + 4 + 10 = 8 + 10 = 18
4 * 10 - 4 = 40 - 4 = 36
(10 - 4) * 4 = 6 * 4 = 24
sure
[" 4 9 11 | 4 9 11 "]
9 + 11 + 4 = 20 + 4 = 24
sure
[" 5 7 8 | 5 7 8 "]
5 + 7 + 8 = 12 + 8 = 20
(8 - 5) * 7 = 3 * 7 = 21
I cannot obtain 24 now, but numbers are within a reasonable range
likely
[" 5 6 6 | 5 6 6 "]
5 + 6 + 6 = 17
(6 - 5) * 6 = 1 * 6 = 6
I cannot obtain 24 now, but numbers are within a reasonable range
likely
[" 10 10 11 | 10 10 11 "]
10 + 10 + 11 = 31
(11 - 10) * 10 = 10
10 10 10 are all too big
impossible
[" 1 3 3 | 1 3 3 "]
1 * 3 * 3 = 9
(1 + 3) * 3 = 12
1 3 3 are all too small
impossible
{(item))}
'''

return_prompt = """verify if the input uses the 4 values exactly once, and equates to 24
Input: [" (1+3)*3 | 12 "]
Values: 4 3 3
Judgement: The equation did not use 4! failed
Input: [" (10+10)*4 | 24 "]
Values: 10 10 4
Judgement: (10+10)*4 = 20*4 = 80 does not equate to 24! failed
Input: [" (6-4)*12 | 24 "]
Values: 6 4 12
Judgement: (6-4)*12 = 2*12 = 24. 6 4 12 each used once. Correct! Return (6-4)*12
Input:  [" (9-3)*4 | 24 "]
Values: 3 4 9
Judgement: (9-3)*4 = 6*4 = 24. 3 4 9 each used once. Correct! Return (9-3)*4
Input: {(item)}
Values: {(input)}
Judgement: 
"""

threenumexample = """example for 3 numbers, you need to translate it to 4 numbers (Script do not contain this line.)
    (0)=FORMAT("[[" {(input)} | {(input)} "]]")
    (1)=FOREACH{(0)}LLM(\""""+propose_prompt+"""\") 
    (2)=FOREACH{(1)}SPLIT(";")
    (3)=FLATTEN{(2)}
    (4)=FOREACH{(3)}LLM(\""""+evaluate_prompt+"""\")
    (5)=FOREACH{(4)}MAP({'impossible': 0.001, 'likely': 1, 'sure': 20})
    (6)=TOP20{(3)}BY{(4)}
    (7)=FOREACH{(6)}LLM(\""""+propose_prompt2+"""\") 
    (8)=FOREACH{(7)}SPLIT(";")
    (9)=FLATTEN{(8)}
    (10)=FOREACH{(9)}LLM(\""""+return_prompt+"""\")
    """

class RKnowledgeableNetworkofThought(BaseScheme):
    
    def prep_const_prompt(self):
        self.knowledge_prompt = f"""{game24context} 

        Consider the {threenumexample}"""+"""
        The above example uses (n)= to denote each step, and provides an example structure that solves the game of 24 for 3 numbers. In particular, it repeats a group of steps 2 times to process 2 numbers into one value each time, which is suitable for 3 number cases. Please use your knowledge to create the corresponding step-by-step solution process for 4 numbers for the game of 24.
        """
        self.script_prompt = """

[Context] %s

[Task]
You have to follow the orders to create a script. 
This script is numbered and contains several orders to be called line-by-line in a sequential order.
Use (index) such as (0), (1),... to represent each line.

You can use LLM Inference: use LLM("Your Instruction") to find the answer.
You can use FORMAT to format a string
You can use FOREACH{(index)}LLM("Your Instruction on {(item)}") to conduct LLM inference on each item of the output (list) of {(index)}. use {(item)} as placeholder for the enumerated items.
You can use FOREACH{(index)}SPLIT(divider) to split each item (string) in {(index)} with the divider.
You can use FOREACH{(index)}MAP({a dictionary}) to map each item to numerical value with keywords
You can use TOP[NUM]{(index_a)}BY{(index_b)} to filter the top [NUM] candidates in {(index_a)} using the values in {(index_b)}.
You can prompt the use of RETURN as a special keyword in the output that breaks the loop of FOREACH and returns what follows as the final answer.

[Example]
Here is one example for 3 numbers
%s

[Knowledge]
This is your expert knowledge for 4 numbers
%s

[Instruction]
Prepare the script for 4 numbers. Use the the above example for 3 numbers for the correct syntax and consider your expert knowledge for 4 numbers. You must expand the examples that which suits 3 numbers to the corresponding examples that fits 4 numbers. You must also increase the number of steps approaprietely for 4 numbers, as given in your expert knowledge.
"""

    def prep_task_spcefics(self):
        pass

    def solve_query(self, query):
        goal_prompt = f'Input: {query}\nContext: {game24context}'
        knowledge = readf("hack/o1knowledge")
        script = readf("hack/o1script")
        cache = {"input": query}  # Store query directly in cache
        
        # Extract all steps from script by finding pattern (N)=...
        steps = re.findall(r'\((\d+)\)=(.*?)(?=\(\d+\)=|$)', script, re.DOTALL)
        steps = [(int(idx), cmd.strip()) for idx, cmd in steps]
        steps.sort(key=lambda x: x[0])  # Sort by index
        
        def _sub(match, current_item=None):
            """Replace {(var)} placeholders with their values from cache."""
            var_name = match.group(1)
            index_str = match.group(2)
            
            if var_name == "item" and current_item is not None:
                value = current_item
            elif var_name in cache:
                value = cache[var_name]
            else:
                return match.group(0)  # Keep original if not found
            
            # Handle indexing if present
            if index_str:
                try:
                    if ':' in index_str:  # Handle slice
                        start, end = index_str.split(':')
                        start = int(start) if start else 0
                        end = int(end) if end else len(value)
                        value = value[start:end]
                    else:
                        value = value[int(index_str)]
                except (IndexError, TypeError):
                    return ""
            
            return str(value)
        
        def parse_items_format(text):
            """Parse [[" ... | ... "], ["...|..."] ] format into a list of items."""
            if not isinstance(text, str):
                return [text]
                
            # Check if it matches the special format
            if text.startswith('[["') and text.endswith('"]]'):
                # Remove the outer brackets
                content = text[1:-1].strip()
                                
                # Extract each ["..."] item
                items = []
                item_pattern = re.compile(r'\["([^"]*)"\]')  # Fixed pattern
                matches = item_pattern.finditer(content)

                for match in matches:
                    items.append(match.group(1).strip())
                
                return items if items else [text]
            
            # Try to interpret as a list
            try:
                result = ast.literal_eval(text)
                if isinstance(result, list):
                    return result
                return [result]
            except (SyntaxError, ValueError):
                return [text]
        
        # Process each step in order
        for step_idx, step_cmd in steps:
            idx_str = str(step_idx)
            print("++++")
            print(f"({idx_str})={step_cmd}")
            
            try:
                # Handle FOREACH with LLM (check this first to avoid overlap with regular LLM)
                if 'FOREACH{' in step_cmd and 'LLM(' in step_cmd:
                    # Extract source index and instruction template
                    foreach_match = re.search(r'FOREACH\{\((\w+)\)\}LLM\((.*?)\)', step_cmd, re.DOTALL)
                    
                    if foreach_match:
                        src_index = foreach_match.group(1)
                        instruction_raw = foreach_match.group(2)
                        
                        # Extract instruction from quotes
                        if instruction_raw.startswith('\\"""') and instruction_raw.endswith('\\"""'):
                            instruction_template = instruction_raw[4:-4]
                        elif instruction_raw.startswith('"') and instruction_raw.endswith('"'):
                            instruction_template = instruction_raw[1:-1]
                        else:
                            instruction_template = instruction_raw
                        
                        # Get source list from cache and parse it properly
                        src_data = cache.get(src_index, [])
                        src_list = parse_items_format(src_data)
                        
                        results = []
                        for item in src_list:
                            # Replace "{(item)}" with current item and other variables
                            item_instruction = re.sub(r'\{\((\w+)\)\}(?:\[([0-9:]+)\])?', 
                                                   lambda match: _sub(match, item), 
                                                   instruction_template)
                            print(f"Item Instruction: {item_instruction}")
                            
                            output = self.llm_answer(item_instruction)
                            print(f"Item Output: {output}")
                            
                            # Check for RETURN keyword
                            if "RETURN" in output:
                                return_match = re.search(r'RETURN\s+(.*)', output, re.DOTALL)
                                if return_match:
                                    return return_match.group(1).strip()
                                else:
                                    return output.replace("RETURN", "").strip()
                            
                            # Add result to results list
                            try:
                                results.append(ast.literal_eval(output))
                            except (SyntaxError, ValueError):
                                results.append(output)
                        
                        # Store results in cache
                        cache[idx_str] = results
                        print(f"FOREACH LLM results: {results}")
                        
                # Handle FORMAT
                elif 'FORMAT(' in step_cmd:
                    format_match = re.search(r'FORMAT\("(.*?)"\)', step_cmd)
                    if format_match:
                        format_str = format_match.group(1)
                        # Replace variables in the format string
                        formatted = re.sub(r'\{\((\w+)\)\}(?:\[([0-9:]+)\])?', 
                                          lambda match: _sub(match), 
                                          format_str)
                        cache[idx_str] = formatted
                        print(f"Formatted: {formatted}")
                
                # Handle regular LLM (do this after FOREACH+LLM to avoid pattern overlap)
                elif 'LLM(' in step_cmd and 'FOREACH{' not in step_cmd:
                    # Extract instruction - handle both regular and triple quotes
                    if '\\"""' in step_cmd:
                        instruction_match = re.search(r'LLM\(\\"""(.*?)\\"""\)', step_cmd, re.DOTALL)
                    else:
                        instruction_match = re.search(r'LLM\("(.*?)"\)', step_cmd)
                    
                    if instruction_match:
                        instruction = instruction_match.group(1)
                        # Replace variables in the instruction
                        instruction = re.sub(r'\{\((\w+)\)\}(?:\[([0-9:]+)\])?', 
                                            lambda match: _sub(match), 
                                            instruction)
                        print(f"LLM Instruction: {instruction}")
                        
                        output = self.llm_answer(instruction)
                        print(f"LLM Output: {output}")
                        
                        # Check for RETURN keyword
                        if "RETURN" in output:
                            output = output.replace("RETURN", "").strip()
                            return output
                        
                        # Store result in cache
                        try:
                            cache[idx_str] = ast.literal_eval(output)
                        except (SyntaxError, ValueError):
                            cache[idx_str] = output
                
                # Handle FOREACH with SPLIT
                elif 'FOREACH{' in step_cmd and 'SPLIT(' in step_cmd:
                    # Extract source index and divider
                    split_match = re.search(r'FOREACH\{\((\w+)\)\}SPLIT\((.*?)\)', step_cmd)
                    if split_match:
                        src_index = split_match.group(1)
                        divider_raw = split_match.group(2)
                        
                        # Extract divider from quotes if present
                        if divider_raw.startswith('"') and divider_raw.endswith('"'):
                            divider = divider_raw[1:-1]
                        else:
                            divider = divider_raw
                        
                        # Get source list from cache and parse it
                        src_data = cache.get(src_index, [])
                        src_list = parse_items_format(src_data)
                        
                        # Split each item in the list
                        results = []
                        for item in src_list:
                            if isinstance(item, str):
                                split_results = item.split(divider)
                                results.append(split_results)
                            else:
                                # Handle non-string items
                                results.append([str(item)])
                        
                        # Store results in cache
                        cache[idx_str] = results
                        print(f"FOREACH SPLIT results: {results}")
                
                # Handle FOREACH with MAP
                elif 'FOREACH{' in step_cmd and 'MAP(' in step_cmd:
                    # Extract source index and mapping dictionary
                    map_match = re.search(r'FOREACH\{\((\w+)\)\}MAP\((.*?)\)', step_cmd)
                    if map_match:
                        src_index = map_match.group(1)
                        map_dict_str = map_match.group(2)
                        
                        # Parse mapping dictionary
                        try:
                            map_dict = ast.literal_eval(map_dict_str)
                        except (SyntaxError, ValueError):
                            print(f"Error parsing map dictionary: {map_dict_str}")
                            continue
                        
                        # Get source list from cache and parse it
                        src_data = cache.get(src_index, [])
                        src_list = parse_items_format(src_data)
                        
                        # Map each item based on keyword matching
                        results = []
                        for item in src_list:
                            item_str = str(item).lower()
                            mapped = False
                            
                            # Search for keywords in the item
                            for keyword, value in map_dict.items():
                                if str(keyword).lower() in item_str:
                                    results.append(value)
                                    mapped = True
                                    break
                            
                            # If no match found, keep original value
                            if not mapped:
                                results.append(item)
                        
                        # Store results in cache
                        cache[idx_str] = results
                        print(f"FOREACH MAP results: {results}")
                
                # Handle TOP filtering
                elif 'TOP' in step_cmd and 'BY' in step_cmd:
                    # Extract num, items index, and values index
                    top_match = re.search(r'TOP(\d+)\{\((\w+)\)\}BY\{\((\w+)\)\}', step_cmd)
                    if top_match:
                        num = int(top_match.group(1))
                        items_index = top_match.group(2)
                        values_index = top_match.group(3)
                        
                        # Get items and values from cache
                        items = cache.get(items_index, [])
                        values = cache.get(values_index, [])
                        
                        # Parse items and values if needed
                        if not isinstance(items, list):
                            items = parse_items_format(items)
                        if not isinstance(values, list):
                            values = parse_items_format(values)
                        
                        # Ensure numeric values for sorting
                        numeric_values = []
                        for val in values:
                            try:
                                numeric_values.append(float(val))
                            except (ValueError, TypeError):
                                numeric_values.append(0.0)
                        
                        # Pair items with values, sort, and select top N
                        pairs = list(zip(items, numeric_values))
                        sorted_pairs = sorted(pairs, key=lambda p: p[1], reverse=True)
                        top_items = [p[0] for p in sorted_pairs[:min(num, len(sorted_pairs))]]
                        
                        # Store results in cache
                        cache[idx_str] = top_items
                        print(f"TOP {num} results: {top_items}")
                
                # Handle FLATTEN operation
                elif 'FLATTEN{' in step_cmd:
                    # Extract source index
                    flatten_match = re.search(r'FLATTEN\{\((\w+)\)\}', step_cmd)
                    if flatten_match:
                        src_index = flatten_match.group(1)
                        nested_list = cache.get(src_index, [])
                        
                        # Make sure we have a list of lists
                        if not isinstance(nested_list, list):
                            nested_list = [nested_list]
                        
                        # Flatten list of lists to single list
                        flattened = []
                        for sublist in nested_list:
                            if isinstance(sublist, list):
                                flattened.extend(sublist)
                            else:
                                flattened.append(sublist)
                        
                        # Store results in cache
                        cache[idx_str] = flattened
                        print(f"FLATTEN results: {flattened}")
                
            except Exception as e:
                logging.error(f"Error processing step ({idx_str}): {str(e)}")
                print(f"Error: {str(e)}")
                traceback.print_exc()
            print(cache)
            input(f'step {step_idx}')
        # Return the final result from the last index
        indices = [int(k) for k in cache.keys() if k.isdigit()]
        if not indices:
            return "No output generated"
        
        final_index = str(max(indices))
        final_result = cache.get(final_index, "")
        logging.info(f'"]"]"]"]"]"]"]"]"]"]"]"] final result: {final_result} ["["["["["["["["["["["["["')
        
        return final_result