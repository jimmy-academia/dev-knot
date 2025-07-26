# python -m examples.yelp.yelp_counting
# Copyright (c) 2023 ETH Zurich.
#                    All rights reserved.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# The source code is adapted from the sorting source code written by
# Nils Blach.
#
# main author: Nils Blach
# contributions: Ales Kubicek

import os
import logging
import datetime
import json
import csv
from collections import Counter
from functools import partial
from typing import Dict, List, Callable, Union
from graph_of_thoughts import controller, language_models, operations, prompter, parser

from tqdm import tqdm

def string_to_list(string: str) -> List[str]:
    """
    Helper function to convert a list encoded inside a string into a Python
    list object of string elements.

    :param string: Input string containing a list.
    :type string: str
    :return: List of string elements.
    :rtype: List[str]
    :raise AssertionError: If input string does not contain a list.
    """

    assert string[0] == "[" and string[-1] == "]", "String is not a list."
    return [
        item.strip().replace("'", "").replace('"', "")
        for item in string[1:-1].split(", ")
    ]


def list_to_freq_dict(lst: List[str]) -> Dict[str, int]:
    """
    Helper function that converts a list of string elements, where each element
    can occur multiple times, into a dictionary, where the elements are the keys
    and the number of their occurrences in the input list is the value.

    :param lst: List of string elements.
    :type lst: List[str]
    :return: Frequency dictionary of string elements.
    :rtype: Dict[str, int]
    """

    return dict(Counter(lst))


def valid_aggregation(state: Dict) -> bool:
    """
    Validate that aggregation is correct (sum of the parts).
    """
    try:
        aggr1 = int(state["aggr1"])
        aggr2 = int(state["aggr2"])
        current = int(state["current"])
        return aggr1 + aggr2 == current
    except Exception:
        return False


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

def test_review_counting(state: Dict) -> bool:
    """
    Test if predicted count equals ground truth.
    """
    try:
        return int(state["current"]) == int(state["ground_truth"])
    except Exception:
        return False


class YelpReviewPrompter(prompter.Prompter):
    """
    YelpReviewPrompter provides the generation of prompts specific to the
    keyword counting example for the language models.

    Inherits from the Prompter class and implements its abstract methods.
    """

    count_prompt_sentence = """<Instruction> Count how many reviews in this list express a positive sentiment. Output only a single integer.</Instruction>

<Approach>
To count the number of positive sentiments follow these steps:
1. Initiate count at 0
2. Iterate through the batch review by review.
3. If the review is a positive review, increment the count value by 1.
</Approach>

<Examples>
Input: [REVIEW_1] A menu that satisfies everyone's cravings! Clean, trendy, and delicious! I definitely recommend going early (before 9 am) as the wait tends to get longer after 9 am! But honestly, it is soooo worth the wait. You will leave there feeling so incredible satisfied! [REVIEW_2] I am a long term frequent customer of this establishment. I just went in to order take out (3 apps) and was told they're too busy to do it. Really? The place is maybe half full at best. Does your dick reach your ass? Yes? Go fuck yourself! I'm a frequent customer AND great tipper. Glad that Kanella just opened. NEVER going back to dmitris!
Output: 1

Input: [REVIEW_1] The pasta was amazing and the service was excellent! [REVIEW_2] The food was great but the service was terrible. [REVIEW_3] I love this place and will definitely come back!
Output: 2
</Examples>

Input:
{input}
Output:
"""


    got_split_prompt = """<Instruction> Split the following list of reviews into 2 batches of approximately equal size.
Only output the final 2 batches in the following format without any additional text or thoughts:
{{
    "Batch 1": (Some review text ..., e.g., "[Review 1] ... [Review 2] ..."),
    "Batch 2": (Some review text ..., e.g., "[Review 6] ... [Review 7] ..."),
}} </Instruction>

<Example>
Input:
[REVIEW_1] Tip: Become a member to see many films for free!  I have seen many films at the International House. I can feel they really love film and respect the many mediums of film. Films are usually shown in the original medium in which they were recorded. This makes for a much different experience than watching the films at home.   The theater is clean and the seating is stadium seating. They hold film festivals and show many rare and foreign films. I've been here multiple times where they have difficulty starting a film. I'm not sure if that is because of the medium or because they aren't prepared.   Anyway; I think Philadelphia is very lucky to have the International House and I suggest becoming a member for free films and special even invites. [REVIEW_2] This is my favorite sushi restaurant in Reno. My kids drive over from Chico.  This is a regular stop for the whole family. [REVIEW_3] Nice food but don't go to this place when their busy time; such as brunch time:))    After we ordered about half hour; our food still not show up and we ask the server that we waiting long time. You know what; our server told us ""you guys only waited 22 mins."" WHat the hell is that answer supposed to be???!!!!  And we ask separate check the guy said ""we dont do separate check when we are busy."" :)) Well... i dont offer tip when you busy then:)))) Who fking cares!! [REVIEW_4] If I could give zero stars I would. This is the worst store in this area. I bought a tree stand and was told I could return the product within 30 days if the stand did not fit our tree. Shortly after Christmas I came by to return a $9 tree stand as it did not fit. I was then told by their manager; Rosa; that their policy has always been all Christmas items are final sale. They wouldn't even consider store credit but just flat out refused to do anything. So; do not trust the person at the checkout counter and definitely avoid any Christmas items as you will not be allowed to return anything. Everything is final sale it seems. So; Kmart Goleta; consider me a permanent loss of a customer. I'd rather go to amazon. At least they understand customer service.
Output: 
{{
    "Batch 1": "[REVIEW_1] Tip: Become a member to see many films for free!  I have seen many films at the International House. I can feel they really love film and respect the many mediums of film. Films are usually shown in the original medium in which they were recorded. This makes for a much different experience than watching the films at home.   The theater is clean and the seating is stadium seating. They hold film festivals and show many rare and foreign films. I've been here multiple times where they have difficulty starting a film. I'm not sure if that is because of the medium or because they aren't prepared.   Anyway; I think Philadelphia is very lucky to have the International House and I suggest becoming a member for free films and special even invites. [REVIEW_2] This is my favorite sushi restaurant in Reno. My kids drive over from Chico.  This is a regular stop for the whole family.",
    "Batch 2": "[REVIEW_3] Nice food but don't go to this place when their busy time; such as brunch time:))    After we ordered about half hour; our food still not show up and we ask the server that we waiting long time. You know what; our server told us ""you guys only waited 22 mins."" WHat the hell is that answer supposed to be???!!!!  And we ask separate check the guy said ""we dont do separate check when we are busy."" :)) Well... i dont offer tip when you busy then:)))) Who fking cares!! [REVIEW_4] If I could give zero stars I would. This is the worst store in this area. I bought a tree stand and was told I could return the product within 30 days if the stand did not fit our tree. Shortly after Christmas I came by to return a $9 tree stand as it did not fit. I was then told by their manager; Rosa; that their policy has always been all Christmas items are final sale. They wouldn't even consider store credit but just flat out refused to do anything. So; do not trust the person at the checkout counter and definitely avoid any Christmas items as you will not be allowed to return anything. Everything is final sale it seems. So; Kmart Goleta; consider me a permanent loss of a customer. I'd rather go to amazon. At least they understand customer service.",
}}
</Example>

Input:
{input}
"""

    got_aggregate_prompt = """<Instruction>
Combine the two integer counts into a single integer by adding them together.
Output only the integer sum.

Counts:
{input1}
{input2}

Output:"""

    got_improve_aggregate_prompt = """<Instruction> The following 2 counts were combined into a third count below. 
However, some mistakes occurred and the third count is incorrect. Please fix the third count so that it contains the correct sum of the first 2 counts.
The correct count is simply the sum of the first 2 counts.

<Example>
Count 1: 3
Count 2: 2
Incorrectly Combined Count: 4
Output: 5

Count 1: 0
Count 2: 1
Incorrectly Combined Count: 0
Output: 1
</Example>

Count 1: {input1}
Count 2: {input2}
Incorrectly Combined Count: {input3}
Output:"""

    tot_improve_prompt = """<Instruction> 
The following count of positive reviews is incorrect. Carefully recount the number of positive reviews in these reviews and provide the correct count.
</Instruction>

<Examples>
Input: [REVIEW_1] The service was great! Friendly staff and quick service. [REVIEW_2] Food was terrible and overpriced. Would not recommend. [REVIEW_3] Best experience I've had in years, will definitely be back!
Incorrect Count: 1
Explanation: Review 1 and 3 are clearly positive with phrases like "great", "friendly", "Best experience", and "will definitely be back". Review 2 is negative with "terrible" and "would not recommend".
Output: 2

Input: [REVIEW_1] Waited over an hour for food that was cold when it arrived. [REVIEW_2] The manager was rude when I complained. [REVIEW_3] The ambiance was nice though.
Incorrect Count: 2
Explanation: Only Review 3 contains a positive sentiment with "nice". Reviews 1 and 2 are negative, mentioning "cold food", "waited over an hour", and "rude".
Output: 1
</Examples>

Input: {input}
Incorrect Count: {incorrect_dict}
Output:"""

    def aggregation_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        """
        Generate an aggregation prompt for the language model.

        :param state_dicts: The thought states that should be aggregated.
        :type state_dicts: List[Dict]
        :param kwargs: Additional keyword arguments.
        :return: The aggregation prompt.
        :rtype: str
        :raise AssertionError: If more than two thought states are provided.
        """
        assert len(state_dicts) <= 2, "Expected 2 states for aggregation prompt."
        if len(state_dicts) == 0:
            state_dicts = [{"current": "{}"}, {"current": "{}"}]
        elif len(state_dicts) == 1:
            state_dicts.append({"current": "{}"})
        return self.got_aggregate_prompt.format(
            input1=state_dicts[0]["current"], input2=state_dicts[1]["current"]
        )

    def generate_prompt(
        self, num_branches: int, original: str, current: str, method: str, **kwargs
    ) -> str:
        """
        Generate a generate prompt for the language model.

        :param num_branches: The number of responses the prompt should ask the LM to generate.
        :type num_branches: int
        :param original: Input text.
        :type original: str
        :param current: Intermediate solution.
        :type current: str
        :param method: Method for which the generate prompt is generated.
        :type method: str
        :param kwargs: Additional keyword arguments.
        :return: The generate prompt.
        :rtype: str
        :raise AssertionError: If the requested number of branches is not one.
        """

        assert num_branches == 1, "Branching should be done via multiple requests."
        if current is None or current == "":
            input = original
        else:
            input = current
        # elif method.startswith("got"):
        if True:
            if (current is None or current == "") and kwargs["phase"] == 0:
                return self.got_split_prompt.format(input=input)

            if kwargs["phase"] == 1:
                return self.count_prompt_sentence.format(input=kwargs["sub_text"])

            if (
                "sub_text" in kwargs
                and kwargs["sub_text"] != ""
                and len(kwargs["sub_text"]) < len(original) * 0.75
            ):
                original = kwargs["sub_text"]
            return self.tot_improve_prompt.format(
                input=original, incorrect_dict=current
            )

    def improve_prompt(self, current: str, aggr1: str, aggr2: str, **kwargs) -> str:
        """
        Generate an improve prompt for the language model.

        :param current: Intermediate solution.
        :type current: str
        :param aggr1: Partially solution 1 before aggregation.
        :type aggr1: str
        :param aggr2: Partially solution 2 before aggregation.
        :type aggr2: str
        :param kwargs: Additional keyword arguments.
        :return: The improve prompt.
        :rtype: str
        """
        return self.got_improve_aggregate_prompt.format(
            input1=aggr1, input2=aggr2, input3=current
        )

    def validation_prompt(self, **kwargs) -> str:
        """
        Generate a validation prompt for the language model.

        :param kwargs: Additional keyword arguments.
        :return: The validation prompt.
        :rtype: str
        """
        pass

    def score_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        """
        Generate a score prompt for the language model.

        :param state_dicts: The thought states that should be scored,
                            if more than one, they should be scored together.
        :type state_dicts: List[Dict]
        :param kwargs: Additional keyword arguments.
        :return: The score prompt.
        :rtype: str
        """
        pass


class YelpReviewParser(parser.Parser):
    """
    YelpReviewParser provides the parsing of language model reponses
    specific to the keyword counting example.

    Inherits from the Parser class and implements its abstract methods.
    """

    def __init__(self) -> None:
        """
        Inits the response cache.
        """
        self.cache = {}

    def strip_answer_json(self, text: str) -> str:
        """
        Helper function to retrieve a text from a json string.

        :param text: Input json string.
        :type text: str
        :return: Retrieved text.
        :rtype: str
        """

        text = text.strip()
        if "Output:" in text:
            text = text[text.index("Output:") + len("Output:") :].strip()
        # find the last "{" and "}" and only keep the text in between including the brackets
        start = text.rfind("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return "{}"
        text = text[start : end + 1]
        try:
            json.loads(text)
            return text
        except:
            return "{}"

    def parse_aggregation_answer(
        self, states: List[Dict], texts: List[str]
    ) -> Union[Dict, List[Dict]]:
        """
        Parse the response from the language model for an aggregation prompt.

        :param states: The thought states used to generate the prompt.
        :type states: List[Dict]
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The new thought states after parsing the respones from the language model.
        :rtype: Union[Dict, List[Dict]]
        :raise AssertionError: If more than two thought states are provided.
        """

        assert len(states) <= 2, "Expected 2 states for aggregation answer."
        if len(states) == 0:
            states = [
                {"current": "{}", "sub_text": ""},
                {"current": "{}", "sub_text": ""},
            ]
        elif len(states) == 1:
            states.append({"current": "{}", "sub_text": ""})
        new_states = []
        for text in texts:
            answer = self.strip_answer_json(text)
            new_state = states[0].copy()
            new_state["sub_text"] = (
                states[0]["sub_text"] if "sub_text" in states[0] else ""
            ) + (states[1]["sub_text"] if "sub_text" in states[1] else "")
            new_state["current"] = answer
            new_state["aggr1"] = states[0]["current"]
            new_state["aggr2"] = states[1]["current"]
            new_states.append(new_state)
        return new_states

    def parse_improve_answer(self, state: Dict, texts: List[str]) -> Dict:
        """
        Parse the response from the language model for an improve prompt.

        :param state: The thought state used to generate the prompt.
        :type state: Dict
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The new thought state after parsing the responses from the language model.
        :rtype: Dict
        :raise AssertionError: If there is not exactly one response text.
        """

        assert len(texts) == 1, "Expected 1 text for improve answer."
        text = texts[0]
        answer = self.strip_answer_json(text)
        new_state = state.copy()
        new_state["current"] = answer
        return new_state

    def parse_generate_answer(self, state: Dict, texts: List[str]) -> List[Dict]:
        """
        Parse the response from the language model for a generate prompt.

        :param state: The thought state used to generate the prompt.
        :type state: Dict
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The new thought states after parsing the respones from the language model.
        :rtype: List[Dict]
        """

        new_states = []
        for text in texts:
            try:
                if (
                    state["method"].startswith("got")
                    and state["current"] == ""
                    and state["phase"] == 0
                ):
                    answer = self.strip_answer_json(text)
                    json_dict = json.loads(answer)
                    if len(json_dict.keys()) != 4 or len(json_dict.keys()) != 8:
                        logging.warning(
                            f"Expected 4 or 8 paragraphs in json, but found {len(json_dict.keys())}."
                        )
                    for key, value in json_dict.items():
                        if "Paragraph" not in key and "Sentence" not in key:
                            logging.warning(
                                f"Expected key to contain 'Paragraph' or 'Sentence', but found {key}."
                            )
                            continue
                        new_state = state.copy()
                        new_state["current"] = ""
                        new_state["sub_text"] = value
                        new_state["phase"] = 1
                        new_state["part"] = key
                        new_states.append(new_state)
                else:
                    answer = self.strip_answer_json(text)
                    new_state = state.copy()
                    new_state["current"] = answer
                    new_state["phase"] = 2
                    new_states.append(new_state)
            except Exception as e:
                logging.error(f"Could not parse step answer: {text}. Error: {e}")
        return new_states

    def parse_validation_answer(self, state: Dict, texts: List[str]) -> bool:
        """
        Parse the response from the language model for a validation prompt.

        :param state: The thought state used to generate the prompt.
        :type state: Dict
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: Whether the thought state is valid or not.
        :rtype: bool
        """
        pass

    def parse_score_answer(self, states: List[Dict], texts: List[str]) -> List[float]:
        """
        Parse the response from the language model for a score prompt.

        :param states: The thought states used to generate the prompt.
        :type states: List[Dict]
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The scores for the thought states.
        :rtype: List[float]
        """
        pass

def got4(all_potential_countries) -> operations.GraphOfOperations:
    """
    Generates the Graph of Operations for the GoT4 method, which splits the text
    into 4 passages.

    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    operations_graph = operations.GraphOfOperations()

    sub_texts = operations.Generate(1, 1)
    operations_graph.append_operation(sub_texts)  # generate the sublists
    sub_paragraphs = []
    for i in range(1, 3):
        paragraph_id = f"Batch {i}"
        sub_text = operations.Selector(
            lambda thoughts, list_id=paragraph_id: [
                thought for thought in thoughts if thought.state["part"] == list_id
            ]
        )
        sub_text.add_predecessor(sub_texts)
        operations_graph.add_operation(sub_text)
        count_sub_text = operations.Generate(1, 10)
        count_sub_text.add_predecessor(sub_text)
        operations_graph.add_operation(count_sub_text)
        score_sub_text = operations.Score(
            1, False, partial(num_errors, all_potential_countries)
        )
        score_sub_text.add_predecessor(count_sub_text)
        operations_graph.add_operation(score_sub_text)
        keep_best_sub_text = operations.KeepBestN(1, False)
        keep_best_sub_text.add_predecessor(score_sub_text)
        operations_graph.add_operation(keep_best_sub_text)

        sub_paragraphs.append(keep_best_sub_text)

    while len(sub_paragraphs) > 1:
        new_sub_paragraphs = []
        for i in range(0, len(sub_paragraphs), 2):
            aggregate = operations.Aggregate(3)
            aggregate.add_predecessor(sub_paragraphs[i])
            aggregate.add_predecessor(sub_paragraphs[i + 1])
            operations_graph.add_operation(aggregate)
            val_im_aggregate = operations.ValidateAndImprove(
                1, True, 3, valid_aggregation
            )
            val_im_aggregate.add_predecessor(aggregate)
            operations_graph.add_operation(val_im_aggregate)
            score_aggregate = operations.Score(
                1, False, partial(num_errors, all_potential_countries)
            )
            score_aggregate.add_predecessor(val_im_aggregate)
            operations_graph.add_operation(score_aggregate)
            keep_best_aggregate = operations.KeepBestN(1, False)
            keep_best_aggregate.add_predecessor(score_aggregate)
            operations_graph.add_operation(keep_best_aggregate)
            new_sub_paragraphs.append(keep_best_aggregate)
        sub_paragraphs = new_sub_paragraphs

    operations_graph.append_operation(operations.GroundTruth(test_review_counting))

    return operations_graph



def run(
    data_ids: List[int],
    methods: List[Callable[[], operations.GraphOfOperations]],
    budget: float,
    lm_name: str,
) -> float:
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
    :return: Spent budget in dollars.
    :rtype: float
    """

    print('running!')

    orig_budget = budget
    data_path = os.path.join(os.path.dirname(__file__), "data/10.csv")
    # data_path = os.path.join(os.path.dirname(__file__), "data/20.csv")
    # data_path = os.path.join(os.path.dirname(__file__), "data/30.csv")
    data = []
    with open(data_path, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            data.append([int(row[0]), row[1], row[2]])

    all_potential_countries = list(
        set([country for row in data for country in row[2][1:-1].split(", ")])
    )

    print('hello')

    if data_ids is None or len(data_ids) == 0:
        data_ids = list(range(len(data)))
    selected_data = [data[i] for i in data_ids]

    results_dir = os.path.join(os.path.dirname(__file__), "results")

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    extra_info = f"{lm_name}_{'-'.join([method.__name__ for method in methods])}"
    folder_name = f"{extra_info}_{timestamp}"
    results_folder = os.path.join(results_dir, folder_name)
    os.makedirs(results_folder)

    print('hello')

    config = {
        "data": selected_data,
        "methods": [method.__name__ for method in methods],
        "lm": lm_name,
        "budget": budget,
    }
    with open(os.path.join(results_folder, "config.json"), "w") as f:
        json.dump(config, f)

    logging.basicConfig(
        filename=os.path.join(results_folder, "log.log"),
        filemode="w",
        format="%(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
    )

    for method in methods:
        # create a results directory for the method
        os.makedirs(os.path.join(results_folder, method.__name__))

    for data in tqdm(selected_data, ncols=88, desc='keyword: iterating...'):
        logging.info(f"Running data {data[0]}: {data[1]}")
        if budget <= 0.0:
            logging.error(
                f"Budget has been depleted, stopping. Data {data[0]} has not been run."
            )
            break
        for method in methods:
            logging.info(f"Running method {method.__name__}")
            logging.info(f"Budget left: {budget}")
            if budget <= 0.0:
                logging.error(
                    f"Budget has been depleted, stopping. Method {method.__name__} has not been run."
                )
                break
            lm = language_models.ChatGPT(
                os.path.join(
                    os.path.dirname(__file__),
                    "../../graph_of_thoughts/language_models/config.json",
                ),
                model_name=lm_name,
                cache=True,
            )
            operations_graph = method(all_potential_countries)
            executor = controller.Controller(
                lm,
                operations_graph,
                YelpReviewPrompter(),
                YelpReviewParser(),
                {
                    "original": data[1],
                    "ground_truth": data[2],
                    "current": "",
                    "phase": 0,
                    "method": method.__name__,
                },
            )
            try:
                executor.run()
            except Exception as e:
                logging.error(f"Exception: {e}")
            path = os.path.join(
                results_folder,
                method.__name__,
                f"{data[0]}.json",
            )
            executor.output_graph(path)
            budget -= lm.cost

    return orig_budget - budget


if __name__ == "__main__":
    """
    Input (x)   : an input text with many occurrences of different countries (names)
    Output (y)  : dict of all countries in the input text with their frequencies
    Correct     : y == correct given list of x (dataset)
    Input Example:
        The music of Spain and the history of Spain deepened her love for Europe...
    Output Example:
        {Spain: 2, ...}
    """
    budget = 30
    samples = [item for item in range(0, 100)]
    # approaches = [io, cot, tot, tot2, got4, got8, gotx]
    approaches = [got4]

    spent = run(samples, approaches, budget, "chatgpt")

    logging.info(f"Spent {spent} out of {budget} budget.")
