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

    def _parse_sets_from_query(self, query: str):
        bracket_matches = re.findall(r"\[([^\]]*)\]", query)
        if len(bracket_matches) >= 2:
            set1_str = "[" + bracket_matches[0].strip() + "]"
            set2_str = "[" + bracket_matches[1].strip() + "]"
            return set1_str, set2_str

        brace_matches = re.findall(r"\{([^}]*)\}", query)
        if len(brace_matches) >= 2:
            set1_str = "{" + brace_matches[0].strip() + "}"
            set2_str = "{" + brace_matches[1].strip() + "}"
            return set1_str, set2_str

        logging.warning(f"[ToP] _parse_sets_from_query: cannot find two sets in query: {query!r}")
        return query, query



    def _define_prompt(self) -> None:
        global COT_TPL, DIVIDE_TPL, MERGE_TPL
        
        base_task = self.args.task.split(':')[0]

        task_for_file = base_task
        if base_task == "set_intersection":
            task_for_file = "set_intersection"

        base_dir = "./schemes/ToP"

        def safe_read(kind, default_str):
            path = f"{base_dir}/{kind}/{task_for_file}.txt"
            try:
                return readf(path)
            except FileNotFoundError:
                logging.warning(f"[ToP] {kind} prompt for {task_for_file} not found, use default inline template.")
                return default_str

        if base_task in ("arithmetic", "addition", "all_arith", "add_mul"):
            COT_TPL = safe_read(
                "cot",
                "You are solving an arithmetic expression.\n"
                "Expression: {input}\n"
                "Think step by step and finally output only the final numeric answer in the last line."
            )
            DIVIDE_TPL = safe_read(
                "divide",
                "You are given an arithmetic expression: {input}\n"
                "Split it into two sub-expressions of length {length_divide} and {length_remain}.\n"
                "Return a Python dict like: {{\"List 1\": [...], \"List 2\": [...]}} with no explanation."
            )
            MERGE_TPL = safe_read(
                "merge",
                "You are given two solved partial results:\n"
                "Part 1 reasoning and result:\n{input_list1}\n\n"
                "Part 2 reasoning and result:\n{input_list2}\n\n"
                "Combine them to get the final answer to the full expression of length {length_combined}.\n"
                "Output only the final numeric answer in the last line."
            )
        elif base_task == "large_digit":
            COT_TPL = safe_read(
                "cot",
                "You are adding two very large integers.\n"
                "Input: {input}\n"
                "Add them digit by digit, then output their sum as an integer in the last line."
            )
            DIVIDE_TPL = safe_read(
                "divide",
                "Given the two large integers in this expression: {input},\n"
                "split the digits (or chunks) into two parts of length {length_divide} and {length_remain}.\n"
                "Return {{\"List 1\": [...], \"List 2\": [...]}} only."
            )
            MERGE_TPL = safe_read(
                "merge",
                "You are given two partial addition results:\n"
                "{input_list1}\n\n{input_list2}\n\n"
                "Merge them to get the final sum of length {length_combined} digits.\n"
                "Output only the final integer in the last line."
            )
        elif base_task == "set_intersection":
            COT_TPL = safe_read(
                "cot",
                "You are finding the intersection of two integer sets.\n"
                "Set1: {set1}\nSet2: {set2}\n"
                "Think step by step and finally output a sorted Python list of the intersection in the last line."
            )
            DIVIDE_TPL = safe_read(
                "divide",
                "Given Set1: {input} (for intersection with Set2), split Set1 into two sublists of length {length_divide} and {length_remain}.\n"
                "Return {{\"List 1\": [...], \"List 2\": [...]}} only."
            )
            MERGE_TPL = safe_read(
                "merge",
                "You are given two partial intersection results as reasoning traces:\n"
                "{input_list1}\n\n{input_list2}\n\n"
                "Merge them to get the final intersection set of length {length_combined}.\n"
                "Output the final intersection as a sorted list in the last line, e.g. [1, 3, 5]."
            )
        else:
            COT_TPL    = safe_read("cot",    "Input: {input}")
            DIVIDE_TPL = safe_read("divide", "Input: {input}")
            MERGE_TPL  = safe_read("merge",  "Input: {input}")

    def _get_sets_from_query(self, query):
        if isinstance(query, dict):
            keys = list(query.keys())
            for k1, k2 in [
                ("Set1", "Set2"),
                ("set1", "set2"),
                ("A", "B"),
                ("list1", "list2"),
            ]:
                if k1 in query and k2 in query:
                    return str(query[k1]), str(query[k2])
            if len(keys) >= 2:
                return str(query[keys[0]]), str(query[keys[1]])

        if isinstance(query, (list, tuple)):
            if len(query) >= 2:
                return str(query[0]), str(query[1])

        if isinstance(query, str):
            bracket_matches = re.findall(r"\[([^\]]*)\]", query)
            if len(bracket_matches) >= 2:
                set1_str = "[" + bracket_matches[0].strip() + "]"
                set2_str = "[" + bracket_matches[1].strip() + "]"
                return set1_str, set2_str
            brace_matches = re.findall(r"\{([^}]*)\}", query)
            if len(brace_matches) >= 2:
                set1_str = "{" + brace_matches[0].strip() + "}"
                set2_str = "{" + brace_matches[1].strip() + "}"
                return set1_str, set2_str

        logging.warning(f"[ToP] _get_sets_from_query: cannot robustly find two sets in query: {query!r}")
        return str(query), str(query)


    def _extract_answer(self, text: str) -> str:
        base_task = self.args.task.split(":")[0]

        if base_task in ["sorting", "set_intersection", "keyword"]:
            for line in reversed(text.strip().splitlines()):
                match = re.search(r"\[[^\]]+\]", line)
                if match:
                    return match.group(0).replace("\\", "")
            # if nothing found, just return the raw last line
            return text.strip().split("\n")[-1]

        elif base_task in ["addition", "arithmetic", "large_digit"]:
            return text.strip().split("\n")[-1].replace(" ", "")

        return "_extract_answer() Error!!!"

    def _divide(self, query: str) -> List[str]:
        length = int(self.args.div)
        base_task = self.args.task.split(":")[0]

        query_for_division = query

        if base_task == "addition":
            length_divide  = math.ceil(length / 2)
        else:
            length_divide  = int(length / 2)
        length_remain = length - length_divide

        prompt = DIVIDE_TPL.format(
            length=length,
            length_divide=length_divide,
            length_remain=length_remain,
            input=query_for_division,
        )

        resp = self.llm_answer(prompt, True)
        print("\nOutput: \n", resp)

        try:
            data = ast.literal_eval(resp)
        except Exception as e:
            logging.error(f"Failed to parse model output: {e}")
            return []

        if base_task in ["sorting", "set_intersection", "addition"]:
            list1_str = str(data.get("List 1", []))
            list2_str = str(data.get("List 2", []))
        elif base_task == "keyword":
            list1_str = str(data.get("Paragraph 1", []))
            list2_str = str(data.get("Paragraph 2", []))
        else:
            list1_str = str(data)
            list2_str = str(data)

        return [list1_str, list2_str]


    def _solve(self, sub: str, set2=None) -> str:
        base_task = self.args.task.split(":")[0]

        if base_task == "set_intersection" and set2 is not None:
            prompt = COT_TPL.format(set1=sub, set2=set2)
        else:
            prompt = COT_TPL.format(input=sub)

        resp = self.llm_answer(prompt, True)
        print("Output: ", resp)
        return resp

    def solve_query(self, query):
        self._define_prompt()
        base_task = self.args.task.split(":")[0]

        print("========== Divide ==========")
        start_time = time.time()

        if base_task == "set_intersection":
            set1_str, set2_str = self._get_sets_from_query(query)
            print("[DEBUG] Set1:", set1_str)
            print("[DEBUG] Set2:", set2_str)
            sub_list = self._divide(set1_str)
        else:
            set2_str = None
            sub_list = self._divide(query)

        print(f"[ToP] Sub-problems = {sub_list}")

        divide_duration = time.time() - start_time
        self.perstep_runtimes.append(divide_duration)

        if len(sub_list) < 2:
            logging.warning(
                f"[ToP] _divide() returned {len(sub_list)} parts; auto-padding to 2 parts."
            )
            if len(sub_list) == 0:
                sub_list = [str(query), str(query)]
            else:
                sub_list = [sub_list[0], sub_list[0]]

        print("========== Solve ==========")
        start_time = time.time()

        solved_lines = []
        for idx, sub in enumerate(sub_list, start=1):
            if base_task == "set_intersection":
                ans = self._solve(sub, set2=set2_str)
            else:
                ans = self._solve(sub)
            solved_lines.append(ans)

        print("[ToP] solved_lines: ", solved_lines)

        solve_duration = time.time() - start_time
        self.perstep_runtimes.append(solve_duration)

        if len(solved_lines) < 2:
            logging.warning(
                f"[ToP] solve phase produced {len(solved_lines)} lines; auto-padding for merge."
            )
            if len(solved_lines) == 0:
                solved_lines = ["", ""]
            else:
                solved_lines = [solved_lines[0], solved_lines[0]]

        print("========== Merge ==========")
        start_time = time.time()

        length = int(self.args.div)
        merge_prompt = MERGE_TPL.format(
            input_list1=solved_lines[0],
            input_list2=solved_lines[1],
            length=int(length / 2),
            length_combined=length,
        )

        final_raw = self.llm_answer(merge_prompt, True)
        print("Output: \n", final_raw)
        final_answer = self._extract_answer(final_raw)
        print("final_answer: ", final_answer)

        merge_duration = time.time() - start_time
        self.perstep_runtimes.append(merge_duration)

        return final_answer
