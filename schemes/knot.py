import re
import ast
from functools import partial

import time
import logging
from .base import BaseScheme
from tqdm import tqdm

Task_Specific_Concept = {
    'healthcare': (
    "You are given a patient case and a rule-based triage workflow. "
    "Each workflow contains if-else logic conditions that reason over vitals, symptoms, comorbidities, and other risk factors. "
    "Follow the logic exactly to determine the correct care recommendation. "
    "Each recommendation must be one of the following: Home care, Outpatient evaluation, Urgent clinical evaluation, ER referral. "
    "Use numerical digits rather than words for all threshold values. "
    "Follow the example to break down the conditional if else into sepearate branches"
),
    'gsm8k': "Solve the final problem to find the sum of the answer to each problems. Solve the problems one by one, then add the answers together.",
    'yelp': "Output how many positive reviews in the input. First summarize the reviews step-by-step, than check every review one by one in the input.",
    'keyword': "Output all words about countries in the article. You can seperate article into sentences first. The maximum number of sentences is 20.",
    'sorting': "Sort input in ascending order. You can use counting sort.",
    'intersection': "Find the intersection of two input. You can check every element in set1 one by one.",
    'arithmetic': """Perform the arithmetic result of input. 
You can only operate two numbers at a time. Calculate from left to right. Do multiplication and division first.""",
    'large_digit': "Calculate the result of the input. You can plus one digit from one digit strating from the least significant digit.",
    'add_mul': """Perform the arithmetic result of input. 
You can only operate two numbers at a time. Calculate from left to right. Do multiplication and division first.""",    
    'addition': "Perform the arithmetic result of input. You can only operate two numbers at a time.",
    'addition2': "Perform the arithmetic result of input. Do not add numbers 1-by-1, add it 2-by-2. You must add two numbers from the list to the tally at each step.",
    'addition3': "Perform the arithmetic result of input. Do not add numbers 1-by-1, add it 3-by-3. You must add three numbers from the list to the tally at each step.",
    'addition4': "Perform the arithmetic result of input. You must process four numbers at a time.",
}

Task_Specific_Example = {
    'healthcare': """example for triage workflow reasoning
(0)=LLM("Extract structured fields from the input. Return a Python dictionary with the following keys: 'oxygen' (int), 'temperature' (float), 'age' (int), 'comorbidities' (list of strings). Input: {(input)}")
(1)=LLM("Is oxygen saturation less than 92? Based on {(0)}. Output 'yes' or 'no'.")
(2)=LLM("Is oxygen saturation less than 95? Based on {(0)}. Output 'yes' or 'no'.")
(3)=LLM("Is temperature greater than 101°F? Based on {(0)}. Output 'yes' or 'no'.")
(4)=LLM("Let Q1 indicate whether oxygen saturation is less than 92. If Q1 = 'yes', then severity = critical. Given Q1 = {(1)}, does this branch apply? Output only one of: applies, does not apply.")
(5)=LLM("If oxygen saturation < 95 OR temperature > 101°F, then severity = moderate. This applies only if Q1 is 'no' and (Q2 is 'yes' OR Q3 is 'yes'). Given Q1={(1)}, Q2={(2)}, Q3={(3)}, does this branch apply? Output only one of: applies, does not apply.")
(6)=LLM("If none of the previous conditions apply, then severity = mild. This applies only if Q1 is 'no', Q2 is 'no', and Q3 is 'no'. Given Q1={(1)}, Q2={(2)}, Q3={(3)}, does this branch apply? Output only one of: applies, does not apply.")
(7)=LLM("Only one severity level should apply. Severity branch outcomes: - critical: {(4)} - moderate: {(5)} - mild: {(6)} Return the first severity level that applies.")
(8)=LLM("Is the patient's age greater than or equal to 70? Use {(0)}. Output 'yes' or 'no'.")
(9)=LLM("{(0)}. Look at the ['comorbidities'] list and count how many items are in it. If the count is greater than or equal to 2, output 'yes'. Otherwise, output 'no'.")
(10)=LLM("Determine risk level using previous answers: If Q1 is 'yes' OR Q2 is 'yes' → risk = high. Else → risk = standard. Use Q1={(8)}, Q2={(9)}. Output only one of: high, standard.")
(11)=LLM("Rephrase the decision logic step as follows: If severity is critical → ER referral. Given severity={(7)} and risk={(10)}, Does this branch applies (applies, does not apply)?")
(12)=LLM("Rephrase the decision logic step as follows: If severity is moderate and risk is high → Urgent clinical evaluation. Given severity={(7)} and risk={(10)}, Does this branch applies (applies, does not apply)?")
(13)=LLM("Rephrase the decision logic step as follows: If severity is moderate and risk is standard → Outpatient evaluation. Given severity={(7)} and risk={(10)}, does this branch applies (applies, does not apply)?")
(14)=LLM("Rephrase the decision logic step as follows: If severity is mild → Home care. Given severity={(7)} and risk={(10)}, does this branch applies (applies, does not apply)?")
(15)=LLM("The result of each branch is: ER referral {(3)}. Urgent clinical evaluation {(4)}. Outpatient evaluation {(5)}. Home care {(6)}. Output the one that is applicable")
""",
    'gsm8k': """example for length = 2
(0)=LLM("Split the into a list of separate problems as : ["Problem 1...", "Problem 2...", ..., "Final Problem: what is the sum of the answers from all of the problems?"] \n {(input)}")
(1)=LLM("{(0)}[0] Let's think step by step.")
(2)=LLM("extract the numerical from the answer: {(1)}")
(3)=LLM("{(0)}[1] Let's think step by step.")
(4)=LLM("extract the numerical from the answer: {(3)}")
(5)=LLM("Combine {(2)} and {(4)}. Only output the number.")""",
    'yelp': """example for length = 3
(0)=LLM("Let's think step-by-step. Summarize the following batch of reviews, review-by-review. Maintain the same sentiment in each summary. Continue to use [review] to delineate: {(input)}")
(1)=LLM("CSplit the following batch of Yelp reviews into separate items. 
Output a Python list where each review is a string element, preserving the [REVIEW_X] tags. Format your response ONLY as a valid Python list like this: ["[REVIEW_1] First review text...", "[REVIEW_2] Second review text...",...] Do not include any explanations or additional text outside the list. Reviews to split: {(0)}")
(2)=LLM("Output Positive or Negative based on the following review sentiment: {(1)}[0].")
(3)=LLM("Output Positive or Negative based on the following review sentiment: {(1)}[1].")
(4)=LLM("Output Positive or Negative based on the following review sentiment: {(1)}[2].")
(5)=LLM("[{(2)}, {(3)}, {(4)}], Count how many result shows that it is a positive review. Only output a number.")""",
    'oldyelp':"""
```example for length = 10
(0)=LLM("Split the following batch of review: '{(input)}'. Output an array.")
(1)=LLM("Check the following review is Positive or Negative: {(0)}[0].")
(2)=LLM("Check the following review is Positive or Negative: {(0)}[1].")
(3)=LLM("Check the following review is Positive or Negative: {(0)}[2].")
...
(9)=LLM("Check the following review is Positive or Negative: {(0)}[length-1].")
(10)=LLM("[{(0)}, {(1)}, {(2)}, {(3)}, {(4)}, {(5)},.... ,{(length-1)}], output the number of Positive.")""",
    'keyword': """
```example length = 20
(0)=LLM("Split the following article into sentences: '{(input)}'. Output an array.")
(1)=LLM("Carefully Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[0]"  Output [] if not exist any country.")
(2)=LLM("Carefully Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[1]"  Output [] if not exist any country.")
(3)=LLM("Carefully Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[2]"  Output [] if not exist any country.")
...
(20)=LLM("Carefully Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[19]"  Output [] if not exist any country.")
(21)=LLM("Combine {(1)}, {(2)}, {(3)}, {(4)}, {(5)}, {(6)}, {(7)}, {(8)}, {(9)}, {(10)}, {(11)}, {(12)}, {(13)}, {(14)}, {(15)}, {(16)}, {(17)}, {(18)}, {(19)}, {(20)} in one list. Repeated is allowed. Don't add quotes around country names.")""",
    'longyelp': """example for length = 10
(0)=LLM("Split the following batch of review: '{(input)}'. Output an array.")
(1)=LLM("Check if the following review is Positive. Example: Input: [REVIEW] A menu that satisfies everyone's cravings! Clean, trendy, and delicious! I definitely recommend going early (before 9 am) as the wait tends to get longer after 9 am! But honestly, it is soooo worth the wait. You will leave there feeling so incredible satisfied! This is a positive review. [REVIEW] I am a long term frequent customer of this establishment. I just went in to order take out (3 apps) and was told they're too busy to do it. Really? The place is maybe half full at best. Does your dick reach your ass? Yes? Go fuck yourself! I'm a frequent customer AND great tipper. Glad that Kanella just opened. NEVER going back to dmitris! Output: Positive Input: {(0)}[0]. Output:")
(2)=LLM("Check if the following review is Positive. Example: [REVIEW] A menu that satisfies everyone's cravings! Clean, trendy, and delicious! I definitely recommend going early (before 9 am) as the wait tends to get longer after 9 am! But honestly, it is soooo worth the wait. You will leave there feeling so incredible satisfied! This is a positive review. [REVIEW] I am a long term frequent customer of this establishment. I just went in to order take out (3 apps) and was told they're too busy to do it. Really? The place is maybe half full at best. Does your dick reach your ass? Yes? Go fuck yourself! I'm a frequent customer AND great tipper. Glad that Kanella just opened. NEVER going back to dmitris! Output: Negative Input: {(0)}[1]. Output:")
(3)=LLM("Check if the following review is Positive. Example: [REVIEW] A menu that satisfies everyone's cravings! Clean, trendy, and delicious! I definitely recommend going early (before 9 am) as the wait tends to get longer after 9 am! But honestly, it is soooo worth the wait. You will leave there feeling so incredible satisfied! This is a positive review. [REVIEW] I am a long term frequent customer of this establishment. I just went in to order take out (3 apps) and was told they're too busy to do it. Really? The place is maybe half full at best. Does your dick reach your ass? Yes? Go fuck yourself! I'm a frequent customer AND great tipper. Glad that Kanella just opened. NEVER going back to dmitris! Output: Negative Input: {(0)}[2]. Output:")
...
(9)=LLM("Check if the following review is Positive. Example: [REVIEW] A menu that satisfies everyone's cravings! Clean, trendy, and delicious! I definitely recommend going early (before 9 am) as the wait tends to get longer after 9 am! But honestly, it is soooo worth the wait. You will leave there feeling so incredible satisfied! This is a positive review. [REVIEW] I am a long term frequent customer of this establishment. I just went in to order take out (3 apps) and was told they're too busy to do it. Really? The place is maybe half full at best. Does your dick reach your ass? Yes? Go fuck yourself! I'm a frequent customer AND great tipper. Glad that Kanella just opened. NEVER going back to dmitris! Output: Negative Input: {(0)}[length-1]. Output:")
(10)=LLM("[{(0)}, {(1)}, {(2)}, {(3)}, {(4)}, {(5)},.... ,{(length-1)}], Count how many result shows that it is a positive review. Only output a number.")""",
    'keyword': """
```example length = 20
(0)=LLM("Split the following article into sentences: '{(input)}'. Output an array.")
(1)=LLM("Carefully Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[0]"  Output [] if not exist any country.")
(2)=LLM("Carefully Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[1]"  Output [] if not exist any country.")
(3)=LLM("Carefully Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[2]"  Output [] if not exist any country.")
...
(20)=LLM("Carefully Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[19]"  Output [] if not exist any country.")
(21)=LLM("Combine {(1)}, {(2)}, {(3)}, {(4)}, {(5)}, {(6)}, {(7)}, {(8)}, {(9)}, {(10)}, {(11)}, {(12)}, {(13)}, {(14)}, {(15)}, {(16)}, {(17)}, {(18)}, {(19)}, {(20)} in one list. Repeated is allowed. Don't add quotes around country names.")""",
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
    'addition2': """example for length = 8 (Script do not contain this line.)
(0)=LLM("Split the sequence {(input)} into a list of numbers. Output a list")
(1)=LLM("Add {(0)}[0], {(0)}[1], {(0)}[2], {(0)}[3]. Only output number.")
(2)=LLM("Add {(1)} and {(0)}[4] and {(0)}[5]. Only output number.")
(3)=LLM("Add {(2)} and {(0)}[6] and {(0)}[7]. Only output number.")""",
    'addition3': """example for length = 9 (Script do not contain this line.)
(0)=LLM("Split the sequence {(input)} into a list of numbers. Output a list")
(1)=LLM("Add {(0)}[0], {(0)}[1], {(0)}[2], {(0)}[3], {(0)}[4], {(0)}[5]. Only output number.")
(2)=LLM("Add {(1)} and {(0)}[6], {(0)}[7], {(0)}[8]. Only output number.")""",
    'addition4': """example for length = 12 (Script do not contain this line.)
(0)=LLM("Split the sequence {(input)} into a list of numbers. Output a list")
(1)=LLM("Add {(0)}[0], {(0)}[1], {(0)}[2], {(0)}[3], {(0)}[4], {(0)}[5], {(0)}[6], {(0)}[7]. Only output number.")
(2)=LLM("Add {(1)} and {(0)}[8], {(0)}[9], {(0)}[10], {(0)}[12]. Only output number.")""",
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
}

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

class kNetworkofThought(BaseScheme):
    
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
        self.system_servent = "You follow orders strictly. Output the answer without any additional information."


    # def llm_answer(self, prompt, planner=False, temperature=0):
    #     model = self.args.planner_llm if planner else self.args.worker_llm
    #     message = [system_struct(self.system_servent), user_struct(prompt)]
    #     return self.llm_call(message, model)

    def prep_task_spcefics(self):
        self.tsp_context = Task_Specific_Concept.get(self.args.task)
        self.tsp_example = Task_Specific_Example.get(self.args.task)

    def solve_query(self, query):
        goal_prompt = f'Input: {query}\nContext: {self.tsp_context}'
        print(goal_prompt)
        print('_'*50)

        knowledge = self.llm_answer(self.knowledge_prompt%goal_prompt, True)
        print(knowledge)
        print('_'*50)

        script_prompt = self.script_prompt%(self.tsp_example, knowledge, goal_prompt)
        script = self.llm_answer(script_prompt, True)
        print(script)
        print('_'*50)
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

            # Record step time using the new method
            start_time = time.time()
            output = self.llm_answer(instruction)
            duration = time.time() - start_time
            self.perstep_runtimes.append(duration)

            try:
                cache[index] = ast.literal_eval(output)
            except:
                cache[index] = output

        iscorrect = self.ground_truth.lower() in output.lower() if self.args.task == 'healthcare' else self.ground_truth == output

        print('ground_truth:', self.ground_truth, 'answer:', output, iscorrect)
        input('finished 1 sample===> pause|')
        return output

