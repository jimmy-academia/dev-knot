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

    "arithmetic": """
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
        self.ps_prompt = (
            "Let's first understand the problem and devise a plan to solve the problem.\n"
            "Then, let's carry out the plan to solve the problem step by step."
        )

    def prep_task_spcefics(self):
        raw_task_name = self.args.task.split(':')[0]

        if raw_task_name == "keyword":
            key = "keyword_counting"
        elif raw_task_name == "yelp":
            key = "review"
        else:
            key = raw_task_name

        template = Task_Specific_Example.get(key)

        if template is None:
            logging.warning(
                f"[ps] No Task_Specific_Example found for task={raw_task_name} (mapped key={key}). "
                f"Using default template."
            )
            template = "Question: %s\nPlan:"

        self.ps_example = template

    def generate_plan(self, query):
        full_prompt = f"{self.ps_prompt}\nQuestion: {query}\nPlan:"
        plan = self.llm_answer(full_prompt)
        steps = [line.strip() for line in plan.split('\n') if line.strip()]
        return steps

    def _format_query_for_template(self, query):
        if isinstance(query, (list, tuple)):
            return ", ".join(str(x) for x in query)
        else:
            return str(query)

    def _extract_final_answer(self, output):
        task_name = self.args.task.split(':')[0]

        if task_name == "keyword":
            return self.llm_answer(
                f"format the answer {output} in a one-line list (square brackets) "
                f"without quotes. example: [Country, Country, Country, ..., Country]"
            )
        elif task_name == "yelp":
            return self.llm_answer(
                f"Based on the {output}, output the number of positive reviews. Output only an integer."
            )
        elif task_name in ["sorting"]:
            return self.llm_answer(
                f"Given the reasoning {output}, extract and output only the final sorted list "
                f"as a Python list. Output list only."
            )
        elif task_name in ["set_intersection"]:
            return self.llm_answer(
                f"Given the reasoning {output}, extract and output only the final intersection "
                f"of the two sets as a sorted Python list. Output list only."
            )
        elif task_name in ["all_arith", "large_digit", "arithmetic", "large_digit"]:
            return self.llm_answer(
                "extract the numerical value of the answer:" + output
            )
        else:
            logging.warning(f"[ps] No specific extraction logic for task '{task_name}'. Returning raw output.")
            return output

    def solve_query(self, query):
        self.prep_task_spcefics()

        plan_steps = self.generate_plan(query)

        query_str = self._format_query_for_template(query)

        template = getattr(self, "ps_example", None)
        if template is None:
            logging.warning("[ps] ps_example is None, using default template.")
            template = "Question: %s\nPlan:"

        try:
            context = template % query_str
        except TypeError:
            logging.warning(
                "[ps] ps_example has format issues with %s. "
                "Falling back to simple concatenation."
            )
            context = f"{template}\nQuestion: {query_str}\nPlan:"

        last_output = ""
        for i, step in enumerate(plan_steps):
            step_prompt = context + f'\nStep {i+1}: {step}'
            output = self.llm_answer(step_prompt)
            logging.info(f'[ps] Answer in step {i+1}: {output}')
            context += f"\nStep {i+1} Output: {output}"
            last_output = output

        final_output = self._extract_final_answer(last_output)
        logging.info(f'[ps] >>>>>>>>>>>>> Final result: {final_output} <<<<<<<<<<<<<')
        return final_output
