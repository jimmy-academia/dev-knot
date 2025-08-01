from .aot_openai import OpenAI, cprint
import os
import json
import logging
from .base import BaseScheme
from utils import readf

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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

Task_Specific_Example = {
    "sorting": """
For example, to sort the numbers {5, 3, 8, 1, 4} in ascending order.
The sorted list should be this format with no additional output **{1, 3, 4, 5, 8}**.
Below would be the task:
Question: %s

""",
    'keyword': """
```example length = 20
(0)=LLM("Split the following article into sentences: '{(input)}'. Output an array.")
(1)=LLM("Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[0]"  Output [] if not exist any country.")
(2)=LLM("Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[1]"  Output [] if not exist any country.")
(3)=LLM("Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[2]"  Output [] if not exist any country.")
...
(20)=LLM("Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[19]"  Output [] if not exist any country.")
(21)=LLM("Combine {(1)}, {(2)}, {(3)}, {(4)}, {(5)}, {(6)}, {(7)}, {(8)}, {(9)}, {(10)}, {(11)}, {(12)}, {(13)}, {(14)}, {(15)}, {(16)}, {(17)}, {(18)}, {(19)}, {(20)} in one array. Repeated is allowed."),
    
The sorted list should be this with no additional output **[Zimbabwe, Norway, Australia, Canada, Zimbabwe]**"""
}


class AlgorithmofThought(BaseScheme):
    """
    Algorithm of Thoughts
    ---------------------

    This class implements the Algorithm of Thoughts (AoT) algorithm. AoT is a
    general-purpose algorithm for solving problems. It is inspired by the
    human thought process and is based on the idea of generating thoughts and
    evaluating them.

    Parameters
    ----------
    num_thoughts : int
        The number of thoughts to generate at each step of the algorithm.
    max_steps : int
        The maximum number of steps to run the algorithm for.
    value_threshold : float
        The minimum value of a thought to be considered valid.
    pruning_threshold : float
        The minimum value of a thought to be considered for caching.
    backtracking_threshold : float
        The minimum value of a thought to be considered for backtracking.
    initial_prompt : str
        The initial prompt to start the algorithm with.
    openai_api_key : str
        The OpenAI API key to use for the algorithm.
    thought_cache : dict
        The cache to use for the algorithm.

    Returns
    -------
    solution : str
        The solution to the problem.

    Examples
    --------
    >>> from aot.main import AoT
    >>> system = "
    ... Use numbers and basic arithmetic operations (+ - * /) to obtain 24. When
    ... considering the next steps, do not choose operations that will result in a
    ... negative or fractional number. In order to help with the calculations, the
    ... numbers in the parenthesis represent the numbers that are left after the
    ... operations and they are in descending order.
    ... Another thing we do is when there are only two numbers left in the parenthesis, we
    ... check whether we can arrive at 24 only by using basic arithmetic operations
    ... (+ - * /). Some examples regarding this idea:
    ... (21 2) no
    ... since 21 + 2 = 23, 21 - 2 = 19, 21 * 2 = 42, 21 / 2 = 10.5, none of which is equal
    ... to 24.
    ... (30 6) 30 - 6 = 24 yes
    ... (8 3) 8 * 3 = 24 yes
    ... (12 8) no
    ... (48 2) 48 / 2 = 24 yes
    ... Most importantly, do not give up, all the numbers that will be given has indeed a
    ... solution.
    ...
    ... 14 8 8 2
    ... "
    >>> dfs = AoT(
    ...     num_thoughts=2,
    ...     max_steps=10,
    ...     value_threshold=1,
    ...     initial_prompt=system,
    ...     openai_api_key="",
    ... )


    """

    def __init__(
        self,
        args,
        task_loader,
        num_thoughts: int = None,
        max_steps: int = None,
        value_threshold: float = None,
        pruning_threshold=0.5,
        backtracking_threshold=0.4,
        initial_prompt=None,
        openai_api_key: str = None,
        thought_cache=None,  # Set to None here
    ):
        """Init method for AoT"""
        if thought_cache is None:
            self.thought_cache = {"accepted": {}, "pruned": {}}
        else:
            self.thought_cache = thought_cache
        super(AlgorithmofThought, self).__init__(args, task_loader)
        self.task = self.args.task
        self.num_thoughts = num_thoughts
        self.max_steps = max_steps
        self.value_threshold = value_threshold
        self.backtracking_threshold = backtracking_threshold
        self.pruning_threshold = pruning_threshold
        self.initial_prompt = initial_prompt
        self.output = []
        self.openai_api_key = openai_api_key
        self.model = OpenAI(api_key=readf('.openaiapi_key').strip())
        self.prep_const_prompt()
        self.prep_task_spcefics()

    def prep_const_prompt(self):
        self.prompt = "Let's think step by step"

    def prep_task_spcefics(self):
        self.context = Task_Specific_Concept.get(self.task) or ""
        self.example = Task_Specific_Example.get(self.task) or ""

    def solve(self):
        """Solve the problem using AoT prompt and dfs search algorithm"""
        try:
            # Run DFS
            self.dfs(self.initial_prompt, 1)

            # Check if any thoughts were generated
            if not self.output:
                logger.error("No valid thoughts were generated during DFS")
                return None

            # Find the best thought and its value
            best_state, best_value = max(self.output, key=lambda x: x[1])

            # Cache the best thought
            self.thought_cache["accepted"][best_state] = best_value

            # Generate the final solution based on the best thought
            solution = self.model.generate_solution(self.initial_prompt, best_state)

            # Display and return the solution
            cprint(f"Solution is {solution}")

            # Write cache to JSON file
            # Change back to 'w' if you want to overwrite the file
            with open("./thought_cache.json", "a") as json_file:
                json.dump(self.thought_cache, json_file)

            return solution if solution else best_state

        except Exception as error:
            logger.error(f"Error in tot_dfs: {error}")

            # Write cache to JSON file even if an error occurs
            # Change back to 'w' if you want to overwrite the file
            with open("./thought_cache_error.json", "a") as json_file:
                json.dump(self.thought_cache, json_file)
            raise error

    def dfs(self, state, step):
        """Depth-first search algorithm"""
        if step > self.max_steps:
            # Check cache before evaluating
            if state in self.thought_cache["accepted"]:
                value = self.thought_cache["accepted"][state]
            elif state in self.thought_cache["pruned"]:
                return
            else:
                thought, value = self.evaluate_thought(state)
                # Cache the evaluated thought
                self.thought_cache["accepted"][state] = value

            self.output.append((state, value))
            return

        # Check cache before generating and filtering
        if state in self.thought_cache["accepted"]:
            thoughts = [state]
        elif state in self.thought_cache["pruned"]:
            return
        else:
            thoughts = self.generate_and_filter_thoughts(state)

        for next_state in thoughts:
            state_value = self.evaluated_thoughts.get(next_state, 0)
            cprint("Entering DFS with state: ", state, " and step: ", step)

            # Cache pruned thoughts
            if state_value <= self.value_threshold:
                self.thought_cache["pruned"][next_state] = state_value
                continue

            # Proceed with DFS
            child = (
                str((state, next_state)) if isinstance(state, str) else str((*state, next_state))
            )
            self.dfs(child, step + 1)

            # Backtracking
            if self.output:
                best_value = max([value for _, value in self.output])
                if best_value < self.backtracking_threshold:
                    self.output.pop()
                    continue
            else:
                continue  # Or handle empty output differently
          
    def generate_and_filter_thoughts(self, state):
        """Generate and filter thoughts"""
        # Check if thoughts for this state are cached
        if state in self.thought_cache["accepted"]:
            cprint(f"Retrieved accepted thoughts from cache for state: {state}")
            return [state]
        elif state in self.thought_cache["pruned"]:
            cprint(f"Retrieved pruned thoughts from cache for state: {state}")
            return []

        # Else generate new thoughts
        thoughts = self.model.generate_thoughts(
            state, self.num_thoughts, self.initial_prompt
        )

        self.evaluated_thoughts = self.model.evaluate_states(
            thoughts, self.initial_prompt
        )

        filtered_thoughts = [
            thought
            for thought in thoughts
            if self.evaluated_thoughts[thought] >= self.pruning_threshold
        ]

        # # If no thoughts were generated, generate new thoughts until at least one valid thought is produced
        # while not filtered_thoughts:
        #     thoughts = self.model.generate_thoughts(
        #         state, self.num_thoughts, self.initial_prompt
        #     )
        #     self.evaluated_thoughts = self.model.evaluate_states(
        #         thoughts, self.initial_prompt
        #     )
        #     filtered_thoughts = [
        #         thought
        #         for thought in thoughts
        #         if self.evaluated_thoughts[thought] >= self.pruning_threshold
        #     ]

        # Cache the filtered thoughts
        for thought in filtered_thoughts:
            self.thought_cache["accepted"][thought] = self.evaluated_thoughts[thought]

        for thought in thoughts:
            if self.evaluated_thoughts[thought] < self.pruning_threshold:
                self.thought_cache["pruned"][thought] = self.evaluated_thoughts[thought]

        cprint("Generated Thoughts: ", thoughts)
        cprint("Evaluated Thoughts: ", self.evaluated_thoughts)

        cprint(f"filtered_thoughts: {filtered_thoughts}")
        return filtered_thoughts

    def evaluate_thought(self, state):
        """Evaluate a thought"""
        # Check if the thought is already in the cache
        if state in self.thought_cache["accepted"]:
            value = self.thought_cache["accepted"][state]
            cprint(f"Retrieved accepted thought value from cache: {value}")
            return state, value
        elif state in self.thought_cache["pruned"]:
            value = 0  # or whatever value you use for pruned thoughts
            cprint(f"Retrieved pruned thought value from cache: {value}")
            return state, value

        # Otherwise, evaluate the thought
        thought = self.model.generate_thoughts(state, 1, self.initial_prompt)
        value = self.model.evaluate_states([state], self.initial_prompt)[state]

        # Update the cache based on the evaluation
        if value >= self.pruning_threshold:
            self.thought_cache["accepted"][str(state)] = value
        else:
            self.thought_cache["pruned"][str(state)] = value

        cprint(f"Evaluated thought: {value}")
        return thought, value
    
    def solve_query(self, query):

        dfs = AlgorithmofThought(
            args=self.args,
            task_loader=self.task_loader,
            num_thoughts=2,
            max_steps=3,
            value_threshold=0.0,
            initial_prompt=self.context+self.example+query,
            openai_api_key=readf('.openaiapi_key').strip(),
        )
        
        result = dfs.solve()
        if result is not None:
            output = self.llm_answer("extract the answer of the sorting task from the output with the numbers in this format {1, 2, 4, 7, 9} and no other additional output:"+result[0])
        else:
            output = 'failed'
        # logging.info(f'>>>>>>>>>>>> Final result: {output} <<<<<<<<<<<<<')
        return output
