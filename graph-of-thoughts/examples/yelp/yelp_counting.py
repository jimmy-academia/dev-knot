# Copyright (c) 2023 ETH Zurich.
#                    All rights reserved.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import logging
import datetime
import json
import csv
from typing import Dict, List, Callable, Union
from graph_of_thoughts import controller, language_models, operations, prompter, parser

def test_review_counting(state: Dict) -> bool:
    """
    Test if predicted count equals ground truth.
    
    :param state: Thought state that represents the final solution.
    :type state: Dict
    :return: Returns whether the solution matches the ground truth.
    :rtype: bool
    """
    try:
        return int(state["current"]) == int(state["ground_truth"])
    except Exception as e:
        logging.error(f"Error in test_review_counting: {e}")
        return False# python -m examples.yelp.yelp_counting


def num_errors(_, state: Dict) -> float:
    """
    Score = absolute difference between predicted and ground truth counts.
    """
    try:
        correct = int(state["ground_truth"])
        predicted = int(state["current"])
        return abs(correct - predicted)
    except Exception:
        return float('inf')


def valid_aggregation(state: Dict) -> bool:
    """
    Helper function to determine whether the aggregation of two intermediate
    solutions produces valid results.

    :param state: Thought state resulting from an aggregation of thoughts.
    :type state: Dict
    :return: Returns whether the aggregation produced valid results.
    :rtype: bool
    """
    try:
        aggr1 = int(state["aggr1"])
        aggr2 = int(state["aggr2"])
        current = int(state["current"])
        
        # Check if current is the sum of aggr1 and aggr2
        return current == aggr1 + aggr2
    except Exception as e:
        logging.error(f"Error in valid_aggregation: {e}")
        return False


class ReviewCountingPrompter(prompter.Prompter):
    """
    Prompter for counting positive Yelp reviews using Graph of Thoughts.
    """
    # Prompt to count positives in a list of reviews
    count_prompt = """<Instruction>
Count how many reviews in this list express a positive sentiment.
A review has positive sentiment if it expresses satisfaction, approval, or enjoyment.
Output only a single integer representing the count of positive reviews.

<Examples>
Input:
[REVIEW_1] This is my favorite sushi restaurant in Reno. My kids drive over from Chico. This is a regular stop for the whole family. [REVIEW_2] Nice food but don't go to this place when their busy time; such as brunch time:)) After we ordered about half hour; our food still not show up and we ask the server that we waiting long time. You know what; our server told us "you guys only waited 22 mins." WHat the hell is that answer supposed to be???!!!! And we ask separate check the guy said "we dont do separate check when we are busy." :)) Well... i dont offer tip when you busy then:)))) Who fking cares!!
Output:
1

Input:
[REVIEW_1] If I could give zero stars I would. This is the worst store in this area. I bought a tree stand and was told I could return the product within 30 days if the stand did not fit our tree. Shortly after Christmas I came by to return a $9 tree stand as it did not fit. I was then told by their manager; Rosa; that their policy has always been all Christmas items are final sale. [REVIEW_2] I come here all the time on lunch breaks. Get the small chopped salad -- it is NOT small and tastes like heaven. Good cocktails too if I'm feeling like a flighty employee :) [REVIEW_3] It always has a strong smell when you open the door plus they aren't friendly or approachable at all.. .I will never go in there again
Output:
1

Input:
[REVIEW_1] Wow. I am not a vegetarian; nor am I a health-food nut (except for my random "diet" binges) but this place is awesome. A co-worker talked me into trying it out one day (by going there and getting me something and putting it in front of me) and she created a monster. I may not order every day but I sure do think about them. And their delicious salads! Every time I go there I am greeted with a smile and there are tons of other people waiting for their food; as well. Good company =) [REVIEW_2] Tip: Become a member to see many films for free! I have seen many films at the International House. I can feel they really love film and respect the many mediums of film. Films are usually shown in the original medium in which they were recorded. This makes for a much different experience than watching the films at home. The theater is clean and the seating is stadium seating. They hold film festivals and show many rare and foreign films.
Output:
2
</Examples>

Input:
{input}

Output:"""

    # Prompt to split the list into 4 batches
    split_prompt = """<Instruction>
Split the following list of reviews into 4 batches of approximately equal size.
Preserve all [REVIEW_X] tags in your output.
Output a JSON object with keys "Batch 1" to "Batch 4" and their corresponding sub-lists, without additional text.

<Examples>
Input:
[REVIEW_1] Tip: Become a member to see many films for free! I have seen many films at the International House. [REVIEW_2] This is my favorite sushi restaurant in Reno. [REVIEW_3] Nice food but don't go to this place when their busy time; such as brunch time:)) [REVIEW_4] If I could give zero stars I would. This is the worst store in this area. [REVIEW_5] I've been here a handful of times and it's always because I don't have time to go to VN Nails near Costco where I prefer to go. [REVIEW_6] I come here all the time on lunch breaks. Get the small chopped salad -- it is NOT small and tastes like heaven. [REVIEW_7] It always has a strong smell when you open the door plus they aren't friendly or approachable at all. [REVIEW_8] Definitely should have read the reviews first. Ordered $100 worth of pizza for a 13 year Olds birthday.
Output:
{
    "Batch 1": "[REVIEW_1] Tip: Become a member to see many films for free! I have seen many films at the International House. [REVIEW_2] This is my favorite sushi restaurant in Reno.",
    "Batch 2": "[REVIEW_3] Nice food but don't go to this place when their busy time; such as brunch time:)) [REVIEW_4] If I could give zero stars I would. This is the worst store in this area.",
    "Batch 3": "[REVIEW_5] I've been here a handful of times and it's always because I don't have time to go to VN Nails near Costco where I prefer to go. [REVIEW_6] I come here all the time on lunch breaks. Get the small chopped salad -- it is NOT small and tastes like heaven.",
    "Batch 4": "[REVIEW_7] It always has a strong smell when you open the door plus they aren't friendly or approachable at all. [REVIEW_8] Definitely should have read the reviews first. Ordered $100 worth of pizza for a 13 year Olds birthday."
}
</Examples>

Input:
{input}

Output:"""

    # Prompt to split the list into 8 batches
    split_prompt8 = """<Instruction>
Split the following list of reviews into 8 batches of approximately equal size.
Preserve all [REVIEW_X] tags in your output.
Output a JSON object with keys "Batch 1" to "Batch 8" and their corresponding sub-lists, without additional text.

<Examples>
Input:
[REVIEW_1] Tip: Become a member to see many films for free! I have seen many films at the International House. [REVIEW_2] This is my favorite sushi restaurant in Reno. [REVIEW_3] Nice food but don't go to this place when their busy time; such as brunch time:)) [REVIEW_4] If I could give zero stars I would. This is the worst store in this area. [REVIEW_5] I've been here a handful of times and it's always because I don't have time to go to VN Nails near Costco where I prefer to go. [REVIEW_6] I come here all the time on lunch breaks. Get the small chopped salad -- it is NOT small and tastes like heaven. [REVIEW_7] It always has a strong smell when you open the door plus they aren't friendly or approachable at all. [REVIEW_8] Definitely should have read the reviews first. Ordered $100 worth of pizza for a 13 year Olds birthday. [REVIEW_9] Wow. I am not a vegetarian; nor am I a health-food nut but this place is awesome. [REVIEW_10] Been here twice now. Both times I ordered a caesar salad with chicken; and both times it was a bust. [REVIEW_11] The food is amazing, best burgers in town! [REVIEW_12] I would avoid this place, terrible service and mediocre food. [REVIEW_13] Great atmosphere and friendly staff. [REVIEW_14] Overpriced for what you get. [REVIEW_15] Highly recommend the breakfast menu. [REVIEW_16] Parking is a nightmare, won't be back.
Output:
{
    "Batch 1": "[REVIEW_1] Tip: Become a member to see many films for free! I have seen many films at the International House. [REVIEW_2] This is my favorite sushi restaurant in Reno.",
    "Batch 2": "[REVIEW_3] Nice food but don't go to this place when their busy time; such as brunch time:)) [REVIEW_4] If I could give zero stars I would. This is the worst store in this area.",
    "Batch 3": "[REVIEW_5] I've been here a handful of times and it's always because I don't have time to go to VN Nails near Costco where I prefer to go. [REVIEW_6] I come here all the time on lunch breaks. Get the small chopped salad -- it is NOT small and tastes like heaven.",
    "Batch 4": "[REVIEW_7] It always has a strong smell when you open the door plus they aren't friendly or approachable at all. [REVIEW_8] Definitely should have read the reviews first. Ordered $100 worth of pizza for a 13 year Olds birthday.",
    "Batch 5": "[REVIEW_9] Wow. I am not a vegetarian; nor am I a health-food nut but this place is awesome. [REVIEW_10] Been here twice now. Both times I ordered a caesar salad with chicken; and both times it was a bust.",
    "Batch 6": "[REVIEW_11] The food is amazing, best burgers in town! [REVIEW_12] I would avoid this place, terrible service and mediocre food.",
    "Batch 7": "[REVIEW_13] Great atmosphere and friendly staff. [REVIEW_14] Overpriced for what you get.",
    "Batch 8": "[REVIEW_15] Highly recommend the breakfast menu. [REVIEW_16] Parking is a nightmare, won't be back."
}
</Examples>

Input:
{input}

Output:"""

    # Prompt to aggregate two integer counts
    aggregate_prompt = """<Instruction>
Combine the two integer counts into a single integer by summing them.
Output only the integer sum.

<Examples>
Input:
Count 1: 2
Count 2: 3
Output:
5

Input:
Count 1: 0
Count 2: 4
Output:
4

Input:
Count 1: 1
Count 2: 1
Output:
2
</Examples>

Count 1: {input1}
Count 2: {input2}

Output:"""

    def generate_prompt(self, num_branches: int, original: str, current: str, method: str, **kwargs) -> str:
        # initial split or counting
        phase = kwargs.get('phase', 0)
        if phase == 0 and method.startswith('got'):
            if method == 'got8':
                return self.split_prompt8.format(input=original)
            return self.split_prompt.format(input=original)
        if phase == 1 or (phase == 0 and not method.startswith('got')):
            # counting phase on a batch
            batch = kwargs.get('sub_list', original)
            return self.count_prompt.format(input=batch)
        return ''

    def aggregation_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        assert len(state_dicts) == 2, "Expected 2 states to aggregate."
        return self.aggregate_prompt.format(
            input1=state_dicts[0]['current'],
            input2=state_dicts[1]['current'],
        )

    def improve_prompt(self, *args, **kwargs) -> str:
        raise NotImplementedError

    def validation_prompt(self, **kwargs) -> str:
        raise NotImplementedError

    def score_prompt(self, *args, **kwargs) -> str:
        raise NotImplementedError


class ReviewCountingParser(parser.Parser):
    """
    Parser for counting positive Yelp reviews.
    """
    def strip_int(self, text: str) -> str:
        """
        Helper function to retrieve an integer from text.
        
        :param text: Text containing an integer.
        :type text: str
        :return: String representation of the integer.
        :rtype: str
        """
        text = text.strip()
        
        # If the text comes with "Output:", extract only what follows
        if "Output:" in text:
            text = text[text.index("Output:") + len("Output:"):].strip()
        
        # Try to extract integers from the text
        import re
        nums = re.findall(r'\b\d+\b', text)
        
        # Return the last integer found or default to 0
        return nums[-1] if nums else '0'

    def parse_generate_answer(self, state: Dict, texts: List[str]) -> List[Dict]:
        new_states = []
        for text in texts:
            try:
                if state.get('phase', 0) == 0 and state['method'].startswith('got'):
                    # splitting phase: parse JSON of batches
                    try:
                        answer = text.strip()
                        if "Output:" in answer:
                            answer = answer[answer.index("Output:") + len("Output:"):].strip()
                        
                        # Find the JSON object in the text
                        start = answer.find('{')
                        end = answer.rfind('}')
                        if start >= 0 and end > start:
                            answer = answer[start:end+1]
                            
                        batches = json.loads(answer)
                    except Exception as e:
                        logging.warning(f"Failed to parse JSON response: {e}")
                        batches = {}
                    
                    expected_batches = 8 if state['method'] == 'got8' else 4
                    if len(batches.keys()) != expected_batches:
                        logging.warning(f"Expected {expected_batches} batches in JSON, but found {len(batches.keys())}.")
                        
                    for batch_id, sub_list in batches.items():
                        if "Batch" not in batch_id:
                            logging.warning(f"Expected batch_id to contain 'Batch', but found {batch_id}.")
                            continue
                        new_state = state.copy()
                        new_state['current'] = ""
                        new_state['sub_list'] = sub_list
                        new_state['phase'] = 1
                        new_state['part'] = batch_id
                        new_states.append(new_state)
                else:
                    # counting phase
                    answer = self.strip_int(text)
                    new_state = state.copy()
                    new_state['current'] = answer
                    new_state['phase'] = 2
                    new_states.append(new_state)
            except Exception as e:
                logging.error(f"Could not parse generate answer: {text}. Error: {e}")
        return new_states

    def parse_aggregation_answer(self, states: List[Dict], texts: List[str]) -> Union[Dict, List[Dict]]:
        """
        Parse the response from the language model for an aggregation prompt.

        :param states: The thought states used to generate the prompt.
        :type states: List[Dict]
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The new thought states after parsing the respones from the language model.
        :rtype: Union[Dict, List[Dict]]
        """
        assert len(states) == 2, "Expected 2 states for aggregation answer."
        
        new_states = []
        for text in texts:
            answer = self.strip_int(text)
            
            # Create new state with combined information
            new_state = states[0].copy()
            new_state['current'] = answer
            new_state['aggr1'] = states[0]['current']
            new_state['aggr2'] = states[1]['current']
            
            # Preserve any sub_text if present
            new_state['sub_text'] = (
                (states[0].get('sub_text', '') or '') + 
                (states[1].get('sub_text', '') or '')
            )
            
            new_states.append(new_state)
            
        return new_states

    def parse_score_answer(self, *args, **kwargs):
        raise NotImplementedError

    def parse_validation_answer(self, *args, **kwargs):
        raise NotImplementedError

    def parse_improve_answer(self, *args, **kwargs):
        raise NotImplementedError


def got4(all_data) -> operations.GraphOfOperations:
    """
    Splits reviews into 4 batches, counts positive reviews, then aggregates.
    
    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    graph = operations.GraphOfOperations()

    # Phase 0: split into 4 batches
    split_op = operations.Generate(1, 1)
    graph.add_operation(split_op)

    # Phase 1: count each batch
    sub_ops = []
    for i in range(1, 5):
        # Select each batch
        sel = operations.Selector(lambda thoughts, list_id=f"Batch {i}":
                                 [t for t in thoughts if t.state.get('part') == list_id])
        sel.add_predecessor(split_op)
        graph.add_operation(sel)

        # Count positive reviews in the batch
        cnt = operations.Generate(1, 1)
        cnt.add_predecessor(sel)
        graph.add_operation(cnt)

        # Score the count
        score = operations.Score(1, False, num_errors)
        score.add_predecessor(cnt)
        graph.add_operation(score)

        # Keep the best count
        keep = operations.KeepBestN(1, False)
        keep.add_predecessor(score)
        graph.add_operation(keep)

        sub_ops.append(keep)

    # Phase 2+: aggregate counts pairwise
    while len(sub_ops) > 1:
        new_sub_ops = []
        for i in range(0, len(sub_ops), 2):
            # Aggregate pairs of counts
            aggregate = operations.Aggregate(1)
            aggregate.add_predecessor(sub_ops[i])
            aggregate.add_predecessor(sub_ops[i + 1])
            graph.add_operation(aggregate)

            # Validate and improve the aggregation
            val_im = operations.ValidateAndImprove(1, True, 3, valid_aggregation)
            val_im.add_predecessor(aggregate)
            graph.add_operation(val_im)

            # Score the aggregated count
            score = operations.Score(1, False, num_errors)
            score.add_predecessor(val_im)
            graph.add_operation(score)

            # Keep the best aggregated count
            keep = operations.KeepBestN(1, False)
            keep.add_predecessor(score)
            graph.add_operation(keep)

            new_sub_ops.append(keep)
        sub_ops = new_sub_ops

    # Final ground truth check
    ground_truth = operations.GroundTruth(test_review_counting)
    ground_truth.add_predecessor(sub_ops[0])
    graph.add_operation(ground_truth)

    return graph


def got8(all_data) -> operations.GraphOfOperations:
    """
    Splits reviews into 8 batches, counts positive reviews, then aggregates.
    
    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    graph = operations.GraphOfOperations()

    # Phase 0: split into 8 batches
    split_op = operations.Generate(1, 1)
    graph.add_operation(split_op)

    # Phase 1: count each batch
    sub_ops = []
    for i in range(1, 9):
        # Select each batch
        sel = operations.Selector(lambda thoughts, list_id=f"Batch {i}":
                                 [t for t in thoughts if t.state.get('part') == list_id])
        sel.add_predecessor(split_op)
        graph.add_operation(sel)

        # Count positive reviews in the batch
        cnt = operations.Generate(1, 1)
        cnt.add_predecessor(sel)
        graph.add_operation(cnt)

        # Score the count
        score = operations.Score(1, False, num_errors)
        score.add_predecessor(cnt)
        graph.add_operation(score)

        # Keep the best count
        keep = operations.KeepBestN(1, False)
        keep.add_predecessor(score)
        graph.add_operation(keep)

        sub_ops.append(keep)

    # Phase 2+: aggregate counts pairwise
    while len(sub_ops) > 1:
        new_sub_ops = []
        for i in range(0, len(sub_ops), 2):
            # Aggregate pairs of counts
            aggregate = operations.Aggregate(1)
            aggregate.add_predecessor(sub_ops[i])
            aggregate.add_predecessor(sub_ops[i + 1])
            graph.add_operation(aggregate)

            # Validate and improve the aggregation
            val_im = operations.ValidateAndImprove(1, True, 3, valid_aggregation)
            val_im.add_predecessor(aggregate)
            graph.add_operation(val_im)

            # Score the aggregated count
            score = operations.Score(1, False, num_errors)
            score.add_predecessor(val_im)
            graph.add_operation(score)

            # Keep the best aggregated count
            keep = operations.KeepBestN(1, False)
            keep.add_predecessor(score)
            graph.add_operation(keep)

            new_sub_ops.append(keep)
        sub_ops = new_sub_ops

    # Final ground truth check
    ground_truth = operations.GroundTruth(test_review_counting)
    ground_truth.add_predecessor(sub_ops[0])
    graph.add_operation(ground_truth)

    return graph


def direct(all_data) -> operations.GraphOfOperations:
    """
    Direct counting without any batching.
    
    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    graph = operations.GraphOfOperations()
    
    # Direct counting
    generate = operations.Generate(1, 1)
    graph.add_operation(generate)
    
    # Score the result
    score = operations.Score(1, False, num_errors)
    score.add_predecessor(generate)
    graph.add_operation(score)
    
    # Keep the best
    keep = operations.KeepBestN(1, False)
    keep.add_predecessor(score)
    graph.add_operation(keep)
    
    # Final ground truth check
    ground_truth = operations.GroundTruth(test_review_counting)
    ground_truth.add_predecessor(keep)
    graph.add_operation(ground_truth)
    
    return graph


def run(data_ids: List[int], methods, budget: float, lm_name: str, review_count: int = 10) -> float:
    """
    Controller function that executes each specified method for each specified
    sample while the budget is not exhausted.

    :param data_ids: Indices of the sample to be run.
    :type data_ids: List[int]
    :param methods: List of functions to generate Graphs of Operations.
    :type methods: Each function generates a Graph of Operation.
    :param budget: Language model budget for the execution in dollars.
    :type budget: float
    :param lm_name: Name of the language model to be used.
    :type lm_name: str
    :param review_count: Number of reviews per instance (10, 20, or 30).
    :type review_count: int
    :return: Spent budget in dollars.
    :rtype: float
    """
    orig_budget = budget
    data_path = os.path.join(os.path.dirname(__file__), f"data/{review_count}.csv")
    data = []
    with open(data_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            data.append([int(row[0]), row[1], row[2]])

    if not data_ids or len(data_ids) == 0:
        data_ids = list(range(len(data)))
    selected_data = [data[i] for i in data_ids if i < len(data)]

    # prepare results folder
    results_dir = os.path.join(os.path.dirname(__file__), 'results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    extra_info = f"{lm_name}_{'-'.join([method.__name__ for method in methods])}"
    folder_name = f"{extra_info}_{timestamp}"
    results_folder = os.path.join(results_dir, folder_name)
    os.makedirs(results_folder)

    # Create config file
    config = {
        "data": [[d[0], d[1][:100] + "...", d[2]] for d in selected_data],  # Truncate for readability
        "methods": [method.__name__ for method in methods],
        "lm": lm_name,
        "budget": budget,
        "review_count": review_count
    }
    with open(os.path.join(results_folder, "config.json"), "w") as f:
        json.dump(config, f, indent=2)

    # Set up logging
    logging.basicConfig(
        filename=os.path.join(results_folder, "log.log"),
        filemode="w",
        format="%(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
    )

    for method in methods:
        # create a results directory for the method
        os.makedirs(os.path.join(results_folder, method.__name__))

    # Optional TQDM for progress display
    try:
        from tqdm import tqdm
        selected_data_iter = tqdm(selected_data, ncols=88, desc=f'yelp-{review_count}: iterating...')
    except ImportError:
        selected_data_iter = selected_data

    for row in selected_data_iter:
        idx, reviews, gt = row
        logging.info(f"Running data {idx}")
        if budget <= 0.0:
            logging.error(f"Budget has been depleted, stopping. Data {idx} has not been run.")
            break
            
        for method in methods:
            logging.info(f"Running method {method.__name__}")
            logging.info(f"Budget left: {budget}")
            if budget <= 0.0:
                logging.error(f"Budget has been depleted, stopping. Method {method.__name__} has not been run.")
                break
                
            lm = language_models.ChatGPT(
                os.path.join(os.path.dirname(__file__), "../../graph_of_thoughts/language_models/config.json"),
                model_name=lm_name,
                cache=True
            )
            
            operations_graph = method(None)
            executor = controller.Controller(
                lm, operations_graph,
                ReviewCountingPrompter(),
                ReviewCountingParser(),
                {"original": reviews, "ground_truth": gt, "current": "", "phase": 0, "method": method.__name__}
            )
            
            try:
                executor.run()
            except Exception as e:
                logging.error(f"Exception: {e}")
                
            path = os.path.join(results_folder, method.__name__, f"{idx}.json")
            executor.output_graph(path)
            
            # Log result
            try:
                with open(path) as f:
                    graph_data = json.load(f)
                    solved = graph_data[-2]["problem_solved"][0]
                    logging.info(f"Data {idx} with method {method.__name__} solved: {solved}")
                    print(f"[Result] ID {idx} | Method {method.__name__} | Solved {solved}")
            except Exception as e:
                logging.error(f"Error reading results: {e}")
                
            budget -= lm.cost

    return orig_budget - budget


if __name__ == '__main__':
    # Change these parameters as needed for your experiments
    data_ids = list(range(5))  # Use first 5 examples only
    methods = [direct, got4, got8]
    budget = 50.0
    lm_name = 'chatgpt'
    review_count = 10  # Options: 10, 20, 30 reviews per example
    
    spent = run(data_ids, methods, budget, lm_name, review_count)
    
    print(f"Experiment completed. Total spent: ${spent:.2f} out of ${budget:.2f}")