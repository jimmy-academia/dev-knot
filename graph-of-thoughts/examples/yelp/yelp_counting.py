# python -m examples.yelp.yelp_counting
# Copyright (c) 2023 ETH Zurich.
#                    All rights reserved.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# main author: Your Name

import os
import logging
import datetime
import json
import csv
from collections import Counter
from typing import Dict, List, Callable, Union
from graph_of_thoughts import controller, language_models, operations, prompter, parser


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


class ReviewCountingPrompter(prompter.Prompter):
    """
    Prompter for counting positive Yelp reviews using Graph of Thoughts.
    """
    # Prompt to count positives in a list of reviews
    count_prompt = """<Instruction>
Count how many reviews in this list express a positive sentiment.  
Output only a single integer.

Input:
{input}

Output:"""

    # Prompt to split the list into 4 batches
    split_prompt = """<Instruction>
Split the following list of reviews into 4 batches of approximately equal size.  
Output a JSON object with keys "Batch 1" to "Batch 4" and their corresponding sub-lists, without additional text.

Input:
{input}

Output:"""

    # Prompt to aggregate two integer counts
    aggregate_prompt = """<Instruction>
Combine the two integer counts into a single integer by summing them.  
Output only the integer.

Counts:
{input1}
{input2}

Output:"""

    def generate_prompt(self, num_branches: int, original: str, current: str, method: str, **kwargs) -> str:
        # initial split or counting
        phase = kwargs.get('phase', 0)
        if phase == 0 and method.startswith('got'):
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
        t = text.strip()
        # extract last integer in text
        nums = [int(s) for s in t.split() if s.isdigit()]
        return str(nums[-1]) if nums else '0'

    def parse_generate_answer(self, state: Dict, texts: List[str]) -> List[Dict]:
        new_states = []
        for text in texts:
            if state.get('phase', 0) == 0 and state['method'].startswith('got'):
                # splitting phase: parse JSON of batches
                try:
                    batches = json.loads(text)
                except:
                    batches = {}
                for batch_id, sub_list in batches.items():
                    st = state.copy()
                    st['sub_list'] = sub_list
                    st['phase'] = 1
                    st['part'] = batch_id
                    new_states.append(st)
            else:
                # counting phase
                answer = self.strip_int(text)
                st = state.copy()
                st['current'] = answer
                st['phase'] = 2
                new_states.append(st)
        return new_states

    def parse_aggregation_answer(self, states: List[Dict], texts: List[str]) -> List[Dict]:
        # sum two integer counts
        new_states = []
        for text in texts:
            answer = self.strip_int(text)
            base = states[0].copy()
            base['current'] = answer
            base['aggr1'] = states[0]['current']
            base['aggr2'] = states[1]['current']
            new_states.append(base)
        return new_states

    def parse_score_answer(self, *args, **kwargs):
        raise NotImplementedError

    def parse_validation_answer(self, *args, **kwargs):
        raise NotImplementedError

    def parse_improve_answer(self, *args, **kwargs):
        raise NotImplementedError


def got4(all_data) -> operations.GraphOfOperations:
    """Splits reviews into 4 batches, counts positive reviews, then aggregates."""
    graph = operations.GraphOfOperations()

    # Phase 0: split into 4 batches
    split_op = operations.Generate(1, 1)
    graph.add_operation(split_op)

    # Phase 1: count each batch
    sub_ops = []
    for i in range(1, 5):
        sel = operations.Selector(lambda thoughts, list_id=f"Batch {i}":
                                  [t for t in thoughts if t.state.get('part') == list_id])
        sel.add_predecessor(split_op)
        graph.add_operation(sel)

        cnt = operations.Generate(1, 1)
        cnt.add_predecessor(sel)
        graph.add_operation(cnt)

        score = operations.Score(1, False, num_errors)
        score.add_predecessor(cnt)
        graph.add_operation(score)

        keep = operations.KeepBestN(1, False)
        keep.add_predecessor(score)
        graph.add_operation(keep)

        sub_ops.append(keep)

    # Phase 2+: aggregate counts pairwise
    while len(sub_ops) > 1:
        new = []
        for a, b in zip(sub_ops[0::2], sub_ops[1::2]):
            ag = operations.Aggregate(1)
            ag.add_predecessor(a)
            ag.add_predecessor(b)
            graph.add_operation(ag)

            vi = operations.ValidateAndImprove(1, False, 1, lambda s: True)  # Simplified validation
            vi.add_predecessor(ag)
            graph.add_operation(vi)

            score = operations.Score(1, False, num_errors)
            score.add_predecessor(vi)
            graph.add_operation(score)

            keep = operations.KeepBestN(1, False)
            keep.add_predecessor(score)
            graph.add_operation(keep)

            new.append(keep)
        sub_ops = new

    # final ground truth check
    graph.add_operation(operations.GroundTruth(test_review_counting))
    return graph


def run(data_ids: List[int], methods, budget: float, lm_name: str) -> float:
    orig_budget = budget
    data_path = os.path.join(os.path.dirname(__file__), "data/10.csv")
    data = []
    with open(data_path, 'r') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            data.append([int(row[0]), row[1], row[2]])

    if not data_ids:
        data_ids = list(range(len(data)))
    selected = [data[i] for i in data_ids]

    # prepare results folder
    results_root = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(results_root, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = os.path.join(results_root, f"{lm_name}_{methods[0].__name__}_{timestamp}")
    os.makedirs(folder)

    for method in methods:
        os.makedirs(os.path.join(folder, method.__name__))

    for row in selected:
        idx, reviews, gt = row
        for method in methods:
            if budget <= 0: break
            lm = language_models.ChatGPT(
                os.path.join(os.path.dirname(__file__), "../../graph_of_thoughts/language_models/config.json"),
                model_name=lm_name,
                cache=True
            )
            graph = method(None)
            executor = controller.Controller(
                lm, graph,
                ReviewCountingPrompter(),
                ReviewCountingParser(),
                {"original": reviews, "ground_truth": gt, "current": "", "phase": 0, "method": method.__name__}
            )
            try:
                executor.run()
            except Exception as e:
                logging.error(f"Error on {idx}-{method.__name__}: {e}")
            out = os.path.join(folder, method.__name__, f"{idx}.json")
            executor.output_graph(out)
            # real-time log
            with open(out) as f:
                graph_data = json.load(f)
                solved = graph_data[-2]["problem_solved"][0]
                print(f"[Result] ID {idx} | Method {method.__name__} | Solved {solved}")
            budget -= lm.cost

    return orig_budget - budget


if __name__ == '__main__':
    spent = run(None, [got4], 50.0, 'chatgpt')
    print(f"Total spent: {spent}")