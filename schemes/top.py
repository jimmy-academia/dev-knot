import re
import ast
from functools import partial
import logging
from .base import BaseScheme
from debug import *
from typing import List
import math
import time

COT_TPL = None
DIVIDE_TPL = None
MERGE_TPL = None

def readf(path):
    with open(path, 'r') as f:
        return f.read()

Task_Specific_Concept = {
    'addition': "Perform the arithmetic result of input. You can only operate two numbers at a time.",
    'arithmetic': """Perform the arithmetic result of input. 
You can only operate two numbers at a time. Calculate from left to right. Do multiplication and division first.""",
    'all_arith':"""Perform the arithmetic result of input. 
You can only operate two numbers at a time. Calculate from left to right. Do multiplication and division first.""",
    'add_mul': """Perform the arithmetic result of input. 
You can only operate two numbers at a time. Calculate from left to right. Do multiplication and division first.""",
    'sorting': "Sort input in ascending order. You can use counting sort.",
    'set_intersection': "Find the intersection of two input. You can check every element in set1 one by one.",
    'keyword': "Output all words about countries in the article. You can seperate article into sentences first. The maximum number of sentences is 20.",
    'review': "Output how many positive reviews in the input. Check every review one by one in the input.",
    'large_digit': "Calculate the result of the input. You can plus one digit from one digit strating from the least significant digit."
}

class TreeOfProblems(BaseScheme):
    
    def prep_const_prompt(self):
        pass

    def prep_task_spcefics(self):
        self.tsp_context = Task_Specific_Concept.get(self.args.task)

    def _define_prompt(self) -> None:
        global COT_TPL, DIVIDE_TPL, MERGE_TPL
        COT_TPL = readf(f"./schemes/ToP/cot/{self.args.task}.txt")
        DIVIDE_TPL = readf(f"./schemes/ToP/divide/{self.args.task}.txt")
        MERGE_TPL = readf(f"./schemes/ToP/merge/{self.args.task}.txt")


    def _extract_answer(self, text: str) -> str:
        """
        Extract content enclosed in square brackets [] from the last line of LLM output (including brackets).
        Example: "...\nMerged list: ['0','1','2']"  →  "['0','1','2']"
        """
        if self.args.task in ["sorting", "intersection", "keyword"]: 
            for line in reversed(text.strip().splitlines()):
                match = re.search(r"\[[^\]]+\]", line)
                if match:                      # Found a pattern like [...]
                    return match.group(0).replace("\\", "")      # Return the string with brackets directly
        elif self.args.task in ["addition"]:
            return text.strip().split("\n")[-1].replace(" ", "")
        return "_extract_answer() Error!!!"

    def _divide(self, query: str) -> List[str]:
        length = int(self.args.div)

        if self.args.task == "intersection":
            # split Set1 for intersection task
            # For intersection task, query is now in dict format {"Set1": [...], "
            if isinstance(query, dict):
                set1 = query["Set1"]
                query_for_division = str(set1)

        if self.args.task == "addition":
            prompt = DIVIDE_TPL.format(length=length, length_divide=math.ceil(length / 2), length_remain=length - math.ceil(length / 2),input=query_for_division if self.args.task == "intersection" else query)
        else: 
            prompt = DIVIDE_TPL.format(length=length, length_divide=int(length / 2), input=query_for_division if self.args.task == "intersection" else query)
        # print(prompt)
        resp   = self.llm_answer(prompt, True)
        print("\nOutput: \n", resp)
        try:
            data = ast.literal_eval(resp)
        except Exception as e:
            logging.error(f"Failed to parse model output: {e}")
            return []

        # Convert list to single string
        if self.args.task in ["sorting", "intersection", "addition"]:
            list1_str = str(data.get("List 1", []))
            list2_str = str(data.get("List 2", []))
        elif self.args.task == "keyword":
            list1_str = str(data.get("Paragraph 1", []))
            list2_str = str(data.get("Paragraph 2", []))

        return [list1_str, list2_str]
    

    def _solve(self, sub: str, set2 = None) -> str:
        if set2:
            prompt = COT_TPL.format(set1=sub, set2=set2)
        else:
            prompt = COT_TPL.format(input=sub)
        # print("prompt: ", prompt)
        resp = self.llm_answer(prompt, True)
        print("Output: ", resp)
        return resp
    # ------------------------------------

    def solve_query(self, query):
        self._define_prompt()

        # Divide
        print("========== Divide ==========")
        start_time = time.time()
        
        sub_list = self._divide(query)
        print(f"Sub-problems = {sub_list}")
        
        divide_duration = time.time() - start_time
        self.perstep_runtimes.append(divide_duration)

        # Solve leaves
        print("========== Solve ==========")
        start_time = time.time()
        
        solved_lines = []
        for idx, sub in enumerate(sub_list, start=1):
            if self.args.task == "intersection":
                # 處理新的字典格式
                if isinstance(query, dict):
                    set2 = query["Set2"]
                else:
                    # 向後兼容舊格式
                    set1, set2 = query.split(" + ")
                ans = self._solve(sub, set2=set2)
            else:
                ans = self._solve(sub)
            solved_lines.append(ans)

        print("solved_lines: ", solved_lines)
        
        solve_duration = time.time() - start_time
        self.perstep_runtimes.append(solve_duration)
        
        # Merge
        print("========== Merge ==========")
        start_time = time.time()

        length = int(self.args.div)
        merge_prompt = MERGE_TPL.format(input_list1=solved_lines[0], input_list2=solved_lines[1], length = length / 2, length_combined = length)
        # print(merge_prompt)
        final_raw    = self.llm_answer(merge_prompt, True)
        print("Output: \n", final_raw)
        final_answer = self._extract_answer(final_raw)
        print("final_answer: ", final_answer)

        merge_duration = time.time() - start_time
        self.perstep_runtimes.append(merge_duration)

        return final_answer
