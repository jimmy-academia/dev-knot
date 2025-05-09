import re
import ast
from functools import partial
import logging
from .base import BaseScheme
from debug import *

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

    def solve_query(self, query):
        goal_prompt = f'Input: {query}\nContext: {self.tsp_context}'
        
        # Step 1: Generate subproblems
        subproblem_prompt = f"Break this problem into subproblems:\n{goal_prompt}"
        subproblems = self.llm_answer(subproblem_prompt, True)

        print("Generated subproblems:")
        print(subproblems)
        
        # Step 2: Solve each subproblem independently
        subproblem_solutions = []
        for i, subproblem in enumerate(subproblems.split('\n')):
            subproblem_solution = self.llm_answer(f"Solve this subproblem step-by-step:\n{subproblem}", True)
            subproblem_solutions.append(subproblem_solution)
            print(f"Solution {i}: {subproblem_solution}")
        
        # Step 3: Combine results into final answer
        final_prompt = f"Combine these subproblem solutions into a final answer:\n{subproblem_solutions}"
        final_answer = self.llm_answer(final_prompt, True)
        
        return final_answer

