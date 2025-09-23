import re
import ast
import os
import time
from functools import partial
import importlib

import logging
from .base import BaseScheme
from debug import *
import graph_of_thoughts as got

# Import graph-of-thoughts modules
try:
    arith_8 = importlib.import_module('graph-of-thoughts.examples.arithmetic.arith_8')
    digit_8 = importlib.import_module('graph-of-thoughts.examples.large_digit.digit_8')
    TREE_OF_THOUGHTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import graph-of-thoughts modules: {e}")
    TREE_OF_THOUGHTS_AVAILABLE = False

class TreeofThought(BaseScheme):
    
    def prep_const_prompt(self):
        self.system_servent = "You follow orders strictly. Output the answer without any additional information."

    def prep_task_spcefics(self):
        example = """"""

        self.script = """"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def solve_query(self, query):
        # Measure total runtime
        start_time = time.time()
        
        task = getattr(self.args, 'task', 'arithmetic')
        
        # Try Graph of Thoughts first
        if TREE_OF_THOUGHTS_AVAILABLE:
            try:
                if task == 'arithmetic':
                    result = self._run_arithmetic_tot(query)
                elif task == 'large_digit':
                    result = self._run_large_digit_tot(query)
            except Exception as e:
                print(f"ToT failed: {e}")
        else:
            raise Exception("Tree of Thoughts not available")

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

    def _run_arithmetic_tot(self, query):
        """Execute arithmetic task using Tree of Thoughts"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'graph-of-thoughts', 
                                   'graph_of_thoughts', 'language_models', 'config.json')
        lm = got.language_models.ChatGPT(config_path, model_name="chatgpt", cache=True)
        
        # Apply timing patch to language model
        lm = self._patch_lm_for_timing(lm)
        
        executor = got.controller.Controller(
            lm,
            arith_8.tot(), 
            arith_8.ArithPrompter(),
            arith_8.ArithParser(),
            {
                "original": query, 
                "current": "", 
                "phase": 0, 
                "method": "tot"
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

    def _run_large_digit_tot(self, query):
        """Execute large digit task using Tree of Thoughts"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'graph-of-thoughts', 
                                   'graph_of_thoughts', 'language_models', 'config.json')
        lm = got.language_models.ChatGPT(config_path, model_name="chatgpt", cache=True)
        
        # Apply timing patch to language model
        lm = self._patch_lm_for_timing(lm)
        
        executor = got.controller.Controller(
            lm,
            digit_8.tot(),
            digit_8.DigitPrompter(),
            digit_8.DigitParser(),
            {
                "original": query, 
                "current": "", 
                "phase": 0, 
                "method": "tot"
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