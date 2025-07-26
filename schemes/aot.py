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
    'keyword_counting': "Output all words about countries in the article. You can seperate article into sentences first. The maximum number of sentences is 20.",
    'yelp': "Output how many positive reviews in the input. Check every review one by one in the input.",
    'large_digit': "Calculate the result of the input. You can plus one digit from one digit starting from the least significant digit."
}

Task_Specific_Example = {
    "arithmetic": '''
For example, to solve the arithmetic problem 3/9/5+5+1/1-4-6.
The final answer should be a float number rounded to two decimal placesif the final answer is a float number with no less than two decimal places **-3.93** (or an integer with no additional output if the final answer is a float number with zeros in the first two decimal places).
Below would be the task:
Question: %s

''',
    'large_digit': '''
For example, to solve the problem 57247728+67594862
The final answer should be an integer with no additional output **124842590**.
Below would be the task:
Question: %s

''',
    "set_intersection": """
For example, to find the intersection of the sets {11, 60, 1, 49, 21, 33, 14, 56, 54, 15, 23, 40, 45, 22, 7, 28, 20, 46, 51, 6, 34, 37, 3, 50, 17, 8, 25, 0, 35, 47, 18, 19} and {31, 11, 4, 63, 38, 58, 59, 24, 61, 14, 32, 39, 27, 46, 48, 19, 52, 57, 50, 56, 3, 2, 53, 29, 5, 37, 62, 41, 36, 12, 49, 16}.
The sorted list should be this format with no additional output **{3, 11, 14, 19, 37, 46, 49, 50, 56}**.
Below would be the task:
Question: %s

""",
    "sorting": """
For example, to sort the numbers {5, 3, 8, 1, 4} in ascending order.
The sorted list should be this format with no additional output **{1, 3, 4, 5, 8}**.
Below would be the task:
Question: %s

""",
    'keyword_counting': """
```example length = 20
(0)=LLM("Split the following article into a list of sentences: '[(input)]'. Output an array.")
(1)=LLM("Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[0]"  Output [] if not exist any country.")
(2)=LLM("Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[1]"  Output [] if not exist any country.")
(3)=LLM("Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[2]"  Output [] if not exist any country.")
...
(20)=LLM("Extract all country names (no continents) in the order of their appearance from the following sentence (repeated is allowed): "{(0)}[19]"  Output [] if not exist any country.")
(21)=LLM("Combine {(1)}, {(2)}, {(3)}, {(4)}, {(5)}, {(6)}, {(7)}, {(8)}, {(9)}, {(10)}, {(11)}, {(12)}, {(13)}, {(14)}, {(15)}, {(16)}, {(17)}, {(18)}, {(19)}, {(20)} in one array. Repeated is allowed."),
    
The sorted list should be this with no additional output **[Zimbabwe, Norway, Australia, Canada, Zimbabwe]**""",
    'yelp':'''
For example, to count the number of the positive reviews from the review list: \n
['""After seeing the Mt. Vesuvious on Man vs. Food I became obsessed with the Franklin Fountain!  What a collossal dissapointment!""\n\nME TOO! It was also MUCH smaller than on TV - guess they made it special for him. It is WAY overpriced. I feel NO need to ever go back there. Just too expensive for ice cream.\n\n1 star because of the ridiculous prices.', ""The best old-fashioned ice cream around. You may see the prices and freak out, but you get enormous scoops of ice cream here, so the price really isn't that bad. The ingredients are all-natural here: Actual chunks of peaches, strawberries, pieces of mint, even pieces of honeycomb in the honey ice cream! The atmosphere is great, and fits in with Old City really well. 90% of the time, you'll have to stand in line for this ice cream, but its worth it. If you love chocolate, I highly recommend the Whirly Berley."", ""If you're gonna be Cash Only, then you need to do 2 things: first, get with the program; we're moving closer and closer to a cashless society...... You lost a sale tonight, and Im sure youve lost a lot more over time, because there are no working ATMs in your immediate area. Secondly, get a freakin ATM in your store to accomodate your potential customers, that you would lose otherwise! You make MORE money with MORE customers, whether its thru plastic or having your own ATM!!"", 'Come on!  This place is over rated!  I had the mt. Vesuvius and it was ordinary!  Coldstones founders favorite is better than that!  I could have saved myself the $10 and gotten bryers ice cream and entenmans brownies and that would have been better.  The place is overly pretentious!  I would definitly not be going back!', ""Haven't here is a while - total disappointment. One scoop of ice cream on a stale cone $6. Quality of ice cream has gone downhill. Used be creamer and richer. Hopefully they can come back"", ""We came here on a frigid day in November. I got the peanut butter brownie sundae, and husband got a cone with 2 scoops. The scoops were really big. \n\nThe sundae was amaze! Super peanut buttery. And the brownies weren't just chopped up cheap cosmic brownies or something (no offense to a cosmic brownie - they have their place), they are warm, moist brownie pieces. Idk what could be better. \n\nIf I lived here, I'd go all the time to try all the different options (and be 128753784 pounds). They have lots of yummy looking sodas, floats and a lot of ice cream flavors, shakes and sundaes. \n\nYou order at the window and then pickup at a side window. Expect a few minute wait after you order, but it's worth it. You don't rush greatness."", ""Maybe it's their Monday night crew or maybe this spot jumped the shark, but my experience last night was not the place I remember just a few years ago. It was staffed with all Gen Z'ers who felt really entitled for tips with the 3 or 4 tip jars you walked by while they struggled to simply scoop a small ice cream into a cone and make a crappy root beer float with a horrible ratio of soda to ice cream and charge  you $15 for it. Never again. Don't believe the hype!"", ""Franklin Fountain has, without a doubt, the best ice cream and milkshakes I've ever eaten.\n\nMy favorite item on the menu (and I've tried a lot) is the Franklin Mint Shake, complete with homemade chocolate from Shane Confectionary (which has the same owners and is a couple doors down) as well as mint from Shane's rooftop, the result is a simultaneity decadent and refreshing milkshake.  The texture of the shake is perfect, frothy and milky but not too thin.  One of the best parts of the shake is when you reach the bottom, there's still lots of chocolate pieces to be enjoyed.\n\nOther shakes\\/ice cream flavors are also quite good.  The coconut ice cream is chock-full of fresh coconut flakes, making for a powerful and delicious flavor.  The Hydrox Cookie is full of chocolate and cream flavors, and also goes quite well in a shake.\n\nAs for sundaes, the Mount Vesuvius and the Franklin Mint are both delicious.  The Mount Vesuvius is a brownie fudge sundae and is supremely rich and delicious.  Brownies are freshly-baked an warm, as is the hot fudge.  Vanilla and chocolate ice cream are the perfect bases for this delicious sundae.  The Franklin Mint features vanilla bean ice cream, topped with hot fudge, crème de menthe sauce, and the same delicious chocolate in the mint shake.  It is great also.\n\nIn the winter, given the chilly temperatures in Philly, Franklin Fountain unveils an innovative and delicious Winter menu.  The S'mores hot milkshake on the winter menu is phenomenal.  This shake features vanilla bean ice cream mixed with  a warm, homemade graham cracker, homemade marshmallows flamed to toasty, and hot fudge.  The end result is a beautiful product that tastes like warm melting ice cream.  It is fantastic as all the flavors come together beautifully.\n\nFranklin may often have a wait, but it is completely worth waiting for every time for the outrageously good milkshakes and sundaes."", 'Today I went to Franklin Fountain for the second time since moving to Philadelphia. While the ice cream is delicious, the experience I had today was far from satisfactory. After waiting in a very long line that extended outside the store and down the street, I finally reached the door. A woman walking along the street walked straight into the store, ignoring the line and cut right in front of me. \n\nAt first, we thought she was meeting someone who was holding a spot for her or in a rush to use the bathroom. When we noticed that this was not the case, my boyfriend said ""excuse me"" twice to the woman, who turned her back and ignored him. I got her attention and said ""excuse me ma\'am, but you\'ve just cut a very long line."" Her response was, ""I\'m deaf."" I repeated my comment to her loud enough that the entire staff could hear. The staff appropriately asked her if she had, indeed, cut the line, to which she responded, ""I\'m mentally ill. I have PTSD."" The staff offered to show her to the end of the line and she responded by saying, ""No, I just want ice cream."" \n\nIn the end, the woman was not forced to wait her turn, like all of the other customers had to, and she even signaled for a man outside to come cut the line with her.  She told him ""They said it\'s ok!"" and he too, rudely cut in front of me and everyone else. \n\nFranklin Fountain needs to learn to respect its customers and enforce common courtesy. I understand that the blame is really on this woman, but I am disappointed and offended that she and was still served. She may very well be mentally ill like she said, but she gives PTSD sufferers who understand how to wait in line a bad name.', ""Hydrox cookie is the original Oreo! And the better looking one  so delicious! All their flavors taste on point and you can't go wrong. Love love this place. Their sister shop, Shane confectionery, has the best ice cream sandwiches. My favorite is the coconut almond cookie ice cream sandwich""]
The final answer should be an integer with no additional output **4**.
Below would be the task:
Question: count the number of the positive reviews from the review list %s
'''
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
        self.model = OpenAI(api_key=readf('.openaiapi_key'))

    def prep_const_prompt(self):
        self.prompt = "Let's think step by step"

    def prep_task_spcefics(self):
        self.context = Task_Specific_Concept.get(self.task)
        self.example = Task_Specific_Example.get(self.task)

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

        # If no thoughts were generated, generate new thoughts until at least one valid thought is produced
        while not filtered_thoughts:
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
        if self.args.task == 'yelp':
            initial_prompt = self.context+self.example+query
        elif self.args.task == 'keyword_counting':
            initial_prompt = self.context+self.example+str(query)
        else:
            initial_prompt = self.context+self.example%str(query)

        dfs = AlgorithmofThought(
            args=self.args,
            task_loader=self.task_loader,
            num_thoughts=2,
            max_steps=3,
            value_threshold=0.0,
            initial_prompt=initial_prompt,
            openai_api_key=readf('.openaiapi_key'),
        )
        result = dfs.solve()
        if result is not None:
            if self.args.task == 'large_digit' or self.args.task == 'arithmetic' or self.args.task == 'yelp':
                output = self.llm_answer("extract the numerical of the answer:"+result[0])
            elif self.args.task == 'sorting':
                output = self.llm_answer("extract the answer of the sorting task from the output with the numbers in this format {1, 2, 4, 7, 9} and no other additional output:"+result[0])
            elif self.args.task == 'set_intersection':
                output = self.llm_answer("extract the answer of the set intersection task from the output with the numbers in this format {1, 2, 4, 7, 9} and no other additional output:"+result[0])
            elif self.args.task == 'keyword_counting':
                output = self.llm_answer("extract the answer of the keyowrd counting task from the output with the keyword list in this format [Zimbabwe, Norway, Australia, Canada, Zimbabwe] and no other additional output:"+result[0])
        else:
            output = 'No answer output by the algo.'
        # logging.info(f'>>>>>>>>>>>> Final result: {output} <<<<<<<<<<<<<')
        return output

