# Copyright (c) 2023 ETH Zurich.
#                    All rights reserved.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# main author: Nils Blach

import os
import logging
import datetime
import json
import csv
from typing import Dict, List, Callable, Union
from graph_of_thoughts import controller, language_models, operations, prompter, parser
from collections import defaultdict

# This is a hack to also allow execution of this file from the examples directory
try:
    from . import utils
except ImportError:
    import utils


class ArithPrompter(prompter.Prompter):
    """
    ArithPrompter provides the generation of prompts specific to the sorting
    example for the language models.

    Inherits from the Prompter class and implements its abstract methods.
    """

    math_prompt = """
<Instruction> Calculate the given sequence. Output only number, no additional text. </Instruction>

<Examples>
Input: 3+5+6/2+4+5*3+2
Output: 32.0

Input: 7+4+7*6+7+3+7+2+7*7+3+3*6+2/5+4
Output: 146.40

Input: 7+6+2+7+3+6+5*2+4+2+4+7+2+4+3*3+3+5+4+7+6+4+6+7+6+5*2*7+7+3+7+7
Output: 215
</Examples>

Input: {input}
"""

    tot_improve_prompt = """
<Instruction> There are some errors in the following calculation sequence. Fine the errors in it and correct it. </Instruction>

<Approach>
To fix the incorrectly answer follow these steps:
1. Check all numbers in the sequence one by one.
2. Attention to the symbol error using.
</Approach>

<Examples>
Input: 3+5+6+2+4+5*3+2
Incorrectly Answer: 39
Reason: Add 2 one more time
Output: 37

Input: 7+4+7*6+7+3+7+2+7*7+3+3*6+2+5+4
Incorrectly Answer: 149
Reason: Forget to add 4, the last number in the sequence
Output: 153

Input: 7+6+2+7+3+6+5*2+4+2+4+7+2+4+3*3+3+5+4+7+6+4+6+7+6+5*2*7+7+3+7+7
Incorrectly Answer: 202
Reason: The incorrectly addition of the first two numbers, remember to add.
Output: 215
</Examples>

Input: {input}
Incorrectly Answer: {incorrectly_calculated}
"""


    got_split_prompt = """
<Instruction> Split the following sequence of 8 numbers into 2 sequence of 4 numbers each, the first sequence should contain the first 4 numbers and the second sequence the second 4 numbers.
Only output the final 2 sequence in the following format without any additional text or thoughts!:
{{
    "sequence 1": "3+4+5*1",
    "sequence 2": "5+2+3*4"
}} </Instruction>

<Example>
Input: 3+5+6+2+4+5*3+2
Output: 
{{
    "sequence 1": "3+5+6+2",
    "sequence 2": "4+5*3+2"
}}
</Example>

Input: {input}
"""

    got_merge_prompt = """
<Instruction> Merge the following 2 final answers.
Only output the final number without any additional text or thoughts!:</Instruction>

<Approach>
To merge the two number, follow these steps:
1. Calculate the answer of 2 numbers
</Approach>

Merge the following two numbers into one answer:
1: {input1}
2: {input2}

Merged answer:
"""

    def aggregation_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        """
        Generate an aggregation prompt for the language model.

        :param state_dicts: The thought states that should be aggregated.
        :type state_dicts: List[Dict]
        :param kwargs: Additional keyword arguments.
        :return: The aggregation prompt.
        :rtype: str
        :raise AssertionError: If not exactly two thought states are provided.
        """
        assert len(state_dicts) == 2, "Expected two states for aggregation prompt."
        return self.got_merge_prompt.format(
            input1=state_dicts[0]["current"],
            input2=state_dicts[1]["current"]
        )

    def generate_prompt(
        self, num_branches: int, original: str, current: str, method: str, **kwargs
    ) -> str:
        """
        Generate a generate prompt for the language model.

        :param num_branches: The number of responses the prompt should ask the LM to generate.
        :type num_branches: int
        :param original: Input list of numbers.
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

        if current is None or current == "":
            input = original
        else:
            input = current
        if method.startswith("io"):
            return self.math_prompt.format(input=input)
        elif method.startswith("tot"):
            if current is None or current == "":
                return self.math_prompt.format(input=input)
            return self.tot_improve_prompt.format(
                input=original,
                incorrectly_calculated=current
            )
        elif method.startswith("got"):
            if current is None or current == "":
                return self.got_split_prompt.format(input=input)
            # if current is just a sublist of the original input, return the split prompt
            if kwargs["phase"] == 1:
                return self.math_prompt.format(input=current)

            if (
                "uncalculated_seq" in kwargs
                and kwargs["uncalculated_seq"] != ""
            ):
                original = kwargs["uncalculated_seq"]

            return self.tot_improve_prompt.format(
                input=original,
                incorrectly_calculated=current
            )

    def improve_prompt(self, **kwargs) -> str:
        """
        Generate an improve prompt for the language model.

        :param kwargs: Additional keyword arguments.
        :return: The improve prompt.
        :rtype: str
        """
        pass

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


class ArithParser(parser.Parser):
    """
    SortingParser provides the parsing of language model reponses specific to
    the sorting example.

    Inherits from the Parser class and implements its abstract methods.
    """

    def __init__(self) -> None:
        """
        Inits the response cache.
        """
        self.cache = {}

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
        :raise AssertionError: If not exactly two thought states are provided.
        """
        assert len(states) == 2, "Expected two states for aggregation answer."
        new_states = []
        for text in texts:
            answers = text.strip().split("\n")
            if any(["Output" in answer for answer in answers]):
                # cut elements until last output is found
                for answer in reversed(answers):
                    if "Output" in answer:
                        answers = answers[answers.index(answer) :]
                        break

            states = sorted(states, key=lambda x: x["part"])
            merged_unsorted_sublists = (
                states[0]["uncalculated_seq"]
                + states[0]["original"][7]
                + states[1]["uncalculated_seq"]
            )
            new_state = states[0].copy()
            new_state["current"] = answers
            new_state["uncalculated_seq"] = merged_unsorted_sublists
            new_states.append(new_state)
        return new_states

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
        #print("Generate answer: ", texts)
        new_states = []
        for text in texts:
            if state["method"] == "got" and state["current"] == "":
                # We expect a json which contains the four lists named "List 1" to "List 4"
                # cut everything until the opening bracket and everything after the closing bracket
                try:
                    text = text[text.index("{") : text.index("}") + 1]
                    text = text.replace("\n", "").replace(" ", "")
                    json_dict = json.loads(text)
                    if len(json_dict.keys()) != 2:
                        logging.warning(
                            f"Expected 2 lists in json, but found {len(json_dict.keys())}."
                        )
                    for key, value in json_dict.items():
                        if "sequence" not in key:
                            logging.warning(
                                f"Expected key to contain 'sequence', but found {key}."
                            )
                            continue
                        new_state = state.copy()
                        new_state["current"] = str(value)
                        new_state["uncalculated_seq"] = str(value)
                        new_state["phase"] = 1
                        new_state["part"] = key
                        new_states.append(new_state)
                except Exception as e:
                    logging.error(
                        f"Could not parse step answer: {text}. Encountered exception: {e}"
                    )
            else:
                answers = text.strip().split("\n")
                if any(["Output" in answer for answer in answers]):
                    # cut elements until last output is found
                    for answer in reversed(answers):
                        if "Output" in answer:
                            answers = answers[answers.index(answer) :]
                            break   
                answers = [
                    answer.replace("Output: ", "")
                    for answer in answers
                ]
                if len(answers) == 0:
                    logging.warning(
                        f"Could not parse step answer: {text}. Returning empty list."
                    )
                    answer = "[]"
                else:
                    if len(answers) > 1:
                        logging.warning(
                            f"Multiple answers found for step answer: {text}. Using the first one."
                        )
                    answer = answers[0]

                new_state = state.copy()
                new_state["current"] = answer
                new_state["phase"] = 2
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
        """
        pass

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


def io() -> operations.GraphOfOperations:
    """
    Generates the Graph of Operations for the IO method.

    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    operations_graph = operations.GraphOfOperations()

    operations_graph.append_operation(operations.Generate(1, 1))
    operations_graph.append_operation(operations.Score(1, False, utils.num_errors))
    operations_graph.append_operation(operations.GroundTruth(utils.test_sorting))

    return operations_graph


def cot() -> operations.GraphOfOperations:
    """
    Generates the Graph of Operations for the CoT method.

    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    operations_graph = operations.GraphOfOperations()

    operations_graph.append_operation(operations.Generate(1, 1))
    operations_graph.append_operation(operations.Score(1, False, utils.num_errors))
    operations_graph.append_operation(operations.GroundTruth(utils.test_sorting))

    return operations_graph


def tot() -> operations.GraphOfOperations:
    """
    Generates the Graph of Operations for the ToT method.
    ToT uses a wider tree, where on each level there are more branches.

    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    operations_graph = operations.GraphOfOperations()

    operations_graph.append_operation(operations.Generate(1, 20))
    operations_graph.append_operation(operations.Score(1, False, utils.num_errors))
    keep_best_1 = operations.KeepBestN(1, False)
    operations_graph.append_operation(keep_best_1)

    for _ in range(1):
        operations_graph.append_operation(operations.Generate(1, 20))
        operations_graph.append_operation(operations.Score(1, False, utils.num_errors))
        keep_best_2 = operations.KeepBestN(1, False)
        keep_best_2.add_predecessor(keep_best_1)
        operations_graph.append_operation(keep_best_2)
        keep_best_1 = keep_best_2

    operations_graph.append_operation(operations.KeepBestN(1, False))
    operations_graph.append_operation(operations.GroundTruth(utils.test_sorting))

    return operations_graph


def tot2() -> operations.GraphOfOperations:
    """
    Generates the Graph of Operations for the ToT2 method.
    ToT2 uses a tree with more levels, but with fewer branches per level.

    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    operations_graph = operations.GraphOfOperations()

    operations_graph.append_operation(operations.Generate(1, 10))
    operations_graph.append_operation(operations.Score(1, False, utils.num_errors))
    keep_best_1 = operations.KeepBestN(1, False)
    operations_graph.append_operation(keep_best_1)

    for _ in range(2):
        operations_graph.append_operation(operations.Generate(1, 10))
        operations_graph.append_operation(operations.Score(1, False, utils.num_errors))
        keep_best_2 = operations.KeepBestN(1, False)
        keep_best_2.add_predecessor(keep_best_1)
        operations_graph.append_operation(keep_best_2)
        keep_best_1 = keep_best_2

    operations_graph.append_operation(operations.KeepBestN(1, False))
    operations_graph.append_operation(operations.GroundTruth(utils.test_sorting))

    return operations_graph


def got() -> operations.GraphOfOperations:
    """
    Generates the Graph of Operations for the GoT method.

    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    operations_graph = operations.GraphOfOperations()

    plans = operations.Generate(1, 1)
    operations_graph.append_operation(plans)  # generate the sublists
    for i in range(1, 3):
        list_id = f"sequence{i}"
        sub_list = operations.Selector(
            lambda thoughts, list_id=list_id: [
                thought for thought in thoughts if thought.state["part"] == list_id
            ]
        )
        sub_list.add_predecessor(plans)
        operations_graph.add_operation(sub_list)
        sort_sub_list = operations.Generate(1, 5)
        sort_sub_list.add_predecessor(sub_list)
        operations_graph.add_operation(sort_sub_list)
        score_sub_list = operations.Score(1, False, utils.num_errors)
        score_sub_list.add_predecessor(sort_sub_list)
        operations_graph.add_operation(score_sub_list)
        keep_best_sub_list = operations.KeepBestN(1, False)
        keep_best_sub_list.add_predecessor(score_sub_list)
        operations_graph.add_operation(keep_best_sub_list)

    final_aggregate = operations.Aggregate(10)
    operations_graph.append_operation(final_aggregate)
    operations_graph.append_operation(operations.Score(1, False, utils.num_errors))
    keep_best_aggregate_final = operations.KeepBestN(1, False)
    operations_graph.append_operation(keep_best_aggregate_final)

    operations_graph.append_operation(operations.Generate(1, 10))
    score_aggr_3 = operations.Score(1, False, utils.num_errors)
    score_aggr_3.add_predecessor(keep_best_aggregate_final)
    operations_graph.append_operation(score_aggr_3)
    operations_graph.append_operation(operations.KeepBestN(1, False))

    operations_graph.append_operation(operations.GroundTruth(utils.test_sorting))

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
    results = defaultdict(list)
    results['accuracy'] = 0
    correct = total = 0

    problem_solved: bool
    final_ans: float

    orig_budget = budget
    data_path = os.path.join(os.path.dirname(__file__), "arith_8.csv")
    data = []
    with open(data_path, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            data.append([int(row[0]), row[1], row[2]])
    
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
        os.makedirs(os.path.join(results_folder, method.__name__))

    for data in selected_data:
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
            operations_graph = method()
            executor = controller.Controller(
                lm,
                operations_graph,
                ArithPrompter(),
                ArithParser(),
                {
                    "original": data[1],
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

            problem_solved, final_ans = executor.output_graph(path)
            final_ans = float(final_ans[0] if type(final_ans) == type([]) else final_ans)
            final_ans = int(final_ans) if final_ans.is_integer() else round(final_ans, 2)

            budget -= lm.cost

            results['query'].append(data[1])
            results['output'].append(str(final_ans))
            results['answer'].append(data[2])
            correct += 1 if problem_solved else 0
            total += 1
            results['accuracy'] = correct/total

    results['info'] = f"Correct: {correct}/Total: {total}"
    utils.dumpj(results, os.path.join(results_folder, "final_result.json"))

    print(f"Correct: {correct}/Total: {total}")

    return orig_budget - budget


if __name__ == "__main__":

    '''
    logging.basicConfig(
        level=logging.DEBUG,           # ★ root=DEBUG
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler("debug.log", "w", encoding="utf-8"),
            logging.StreamHandler(),   # 同時印到螢幕
        ],
        force=True,                    # ★ 強制覆寫舊 handler
    )
    '''



    budget = 3
    samples = [item for item in range(0, 10)]
    # approaches = [io, tot, got]
    approaches = [got]

    spent = run(samples, approaches, budget, "chatgpt")

    logging.info(f"Spent {spent} out of {budget} budget.")
