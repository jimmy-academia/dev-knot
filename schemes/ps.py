import logging
from .base import BaseScheme

Task_Specific_Example = {
    "sorting": """
Let's first understand this sorting problem and extract the items that need to be sorted.
Then, let's devise a plan to accomplish the sorting, and step by step execute this plan, recording the current sorted state after each movement or comparison of elements, until all items are arranged in the required order.
Finally, please present the list of items after sorting is complete (pay attention to correct comparison and sorting logic).
Question: %s
Plan:""",

    "set_intersection": """
First, let's understand the problem that requires finding the common elements in two lists, and extract these two lists that need to be compared.
Then, let's devise a plan to perform this comparison and identify the common elements step by step, and carry out this plan step by step, recording the common elements found until the comparison is complete.
Finally, please present the final intersection result.
Question: %s
Plan:""",

    "all_arith": """
First, let's understand the problem that requires performing arithmetic operations on a series of numbers, and extract these numbers and the required operations. Then, let's devise a plan to execute these operations and carry out the plan step by step, recording the current intermediate results after each step or multiple steps until all necessary operations are completed.
Finally, please present the final calculated result (please pay attention to the correct order of operations and calculation logic).
Question: %s
Plan:""",

    "large_digit": """
Let's first understand this problem of adding two large numbers, and extract the two numbers that need to be added.
Then, let's devise a plan to accomplish the addition, and step by step execute this plan, recording the current partial sum and carry-over after adding the digits of the same place value and handling the carry-over, until all place values are added.
Finally, please present the final sum result (pay attention to correct place value alignment and carry-over logic).
Question: %s
Plan:""",
    "review": """
Let's first understand this problem of determining the number of positive reviews in a given list. We need to extract individual reviews from the provided data and analyze their sentiment.
Then, let's devise a plan to accomplish this classification. Step by step, we will process each review, identifying key sentiment indicators, such as positive or negative words, contextual cues, and overall sentiment polarity. If a review is classified as positive, we increment our count of positive reviews.
Finally, please present the total count of positive reviews. (Ensure correct handling of punctuation, negations, and contextual meanings to improve accuracy.)
Question: %s
Plan:""" ,
    "keyword_counting": """ Let's first understand this problem of extracting countries mentioned in the text and collect all the countries that appear in the article.
We need to focus on identifying every country name mentioned, ensuring that all instances are captured correctly. We will make sure to include each country in the final list, whether it is repeated or mentioned only once.
After identifying all the countries, we will compile and output the final result as a list of countries. Output the result as a list containing all the country names mentioned in the text.

Question: %s
Plan:

"""
}

class PlanAndSolve(BaseScheme):

    def prep_const_prompt(self):
        self.ps_prompt = """Let's first understand the problem and devise a plan to solve the problem.
Then, let's carry out the plan to solve the problem step by step."""

    def prep_task_spcefics(self):
        self.ps_example = Task_Specific_Example.get(self.args.task)

    def generate_plan(self, query):
        full_prompt = f"{self.ps_prompt}\n{query}\nPlan:"
        plan = self.llm_answer(full_prompt)
        steps = [line.strip() for line in plan.split('\n') if line.strip()]
        return steps

    def solve_query(self, query):
        self.prep_task_spcefics()
        plan_steps = self.generate_plan(query)
        # context = self.ps_example % query
        context = self.ps_example % ", ".join(query)

        for i, step in enumerate(plan_steps):
            output = self.llm_answer(context + f'\nStep {i+1}: {step}')
            logging.info(f'Answer in step {i+1}: {output}')
            context += f"\n{output}"

        final_output = self.llm_answer("extract the numerical of the answer:" + output)
        logging.info(f'>>>>>>>>>>>> Final result: {final_output} <<<<<<<<<<<<<')
        return final_output