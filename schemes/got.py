import re
import ast
import os
import time
from functools import partial
import importlib

import logging
from .base import BaseScheme
from debug import *
# Add the graph_of_thoughts directory to Python path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'graph_of_thoughts'))

import graph_of_thoughts as got

# Import graph-of-thoughts modules
try:
    import examples.arithmetic.arith_8 as arith_8
    import examples.large_digit.digit_8 as digit_8
    GRAPH_OF_THOUGHTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import graph-of-thoughts modules: {e}")
    GRAPH_OF_THOUGHTS_AVAILABLE = False

class GraphofThought(BaseScheme):

    def prep_const_prompt(self):
        self.system_servent = "You follow orders strictly. Output the answer without any additional information."

    def prep_task_spcefics(self):
        example = """Input: [REVIEW_1] A menu that satisfies everyone's cravings! Clean, trendy, and delicious! I definitely recommend going early (before 9 am) as the wait tends to get longer after 9 am! But honestly, it is soooo worth the wait. You will leave there feeling so incredible satisfied! [REVIEW_2] I am a long term frequent customer of this establishment. I just went in to order take out (3 apps) and was told they're too busy to do it. Really? The place is maybe half full at best. Does your dick reach your ass? Yes? Go fuck yourself! I'm a frequent customer AND great tipper. Glad that Kanella just opened. NEVER going back to dmitris! Output: 1 Input: [REVIEW_1] The pasta was amazing and the service was excellent! [REVIEW_2] The food was great but the service was terrible. [REVIEW_3] I love this place and will definitely come back. Output: 2"""

        self.script = """(0)=LLM("Split the following batch of review into two: {(input)}. Output an array.")
(1)=LLM("Count how many review in the following batch is Positive: """+example+""" Input {(0)}[0] Output:")
(2)=LLM("Count how many review in the following batch is Positive: """+example+""" Input {(0)}[0] Output:")
(3)=LLM("Combine the two integer counts into a single integer by adding them together. Output only the integer sum. Counts: {(1)} {(2)}. Output")
"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def solve_query(self, query):
        # Measure total runtime
        start_time = time.time()
        
        task = getattr(self.args, 'task', 'arithmetic')
        
        # Try Graph of Thoughts first
        if GRAPH_OF_THOUGHTS_AVAILABLE:
            try:
                if task == 'arithmetic':
                    result = self._run_arithmetic_got(query)
                elif task == 'large_digit':
                    result = self._run_large_digit_got(query)
            except Exception as e:
                print(f"GoT failed: {e}")
        else:
            raise Exception("Graph of Thoughts not available")

        # Record total runtime
        end_time = time.time()
        self.total_runtimes.append(end_time - start_time)
        
        return result

    def _patch_lm_for_timing(self, lm):
        """Monkey patch the language model to measure per-step runtime"""
        original_chat = lm.chat
        
        def timed_chat(*args, **kwargs):
            step_start_time = time.time()
            result = original_chat(*args, **kwargs)
            step_end_time = time.time()
            self.perstep_runtimes.append(step_end_time - step_start_time)
            return result
        
        lm.chat = timed_chat
        return lm

    def _run_arithmetic_got(self, query):
        """Execute arithmetic task using Graph of Thoughts"""
        config_path = os.path.join(os.path.dirname(__file__), 'graph-of-thoughts', 
                                   'graph_of_thoughts', 'language_models', 'config.json')
        lm = got.language_models.ChatGPT(config_path, model_name="chatgpt", cache=True)
        
        # Apply timing patch to language model
        lm = self._patch_lm_for_timing(lm)
        
        executor = got.controller.Controller(
            lm,
            arith_8.got(),
            arith_8.ArithPrompter(),
            arith_8.ArithParser(),
            {
                "original": query, 
                "current": "", 
                "phase": 0, 
                "method": "got"
            }
        )

        executor.run()
        
        # Extract result
        final_thoughts = executor.get_final_thoughts()
        if final_thoughts and len(final_thoughts) > 0 and len(final_thoughts[-1]) > 0:
            final_thought = final_thoughts[-1][0]
            if 'current' in final_thought.state:
                result = final_thought.state['current']
                return result[0] if isinstance(result, list) and result else result
        return None

    def _run_large_digit_got(self, query):
        """Execute large digit task using Graph of Thoughts"""
        config_path = os.path.join(os.path.dirname(__file__), 'graph-of-thoughts', 
                                   'graph_of_thoughts', 'language_models', 'config.json')
        lm = got.language_models.ChatGPT(config_path, model_name="chatgpt", cache=True)
        
        # Apply timing patch to language model
        lm = self._patch_lm_for_timing(lm)
        
        executor = got.controller.Controller(
            lm,
            digit_8.got(),
            digit_8.DigitPrompter(),
            digit_8.DigitParser(),
            {
                "original": query, 
                "current": "", 
                "phase": 0, 
                "method": "got"
            }
        )

        executor.run()
        
        # Extract result
        final_thoughts = executor.get_final_thoughts()
        if final_thoughts and len(final_thoughts) > 0 and len(final_thoughts[-1]) > 0:
            final_thought = final_thoughts[-1][0]
            if 'current' in final_thought.state:
                result = final_thought.state['current']
                return result[0] if isinstance(result, list) and result else result
        return None