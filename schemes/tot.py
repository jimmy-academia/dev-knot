import os
import time
import importlib
import logging
import re 

from .base import BaseScheme
from .cot import ChainofThought  

# graph_of_thoughts import removed as it is unused in ToT
got = None

logger = logging.getLogger(__name__)

TREE_OF_THOUGHTS_AVAILABLE = True

class TreeofThought(BaseScheme):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_runtimes = []
        self.perstep_runtimes = []
        self._cot_helper = None

    def prep_const_prompt(self):
        self.system_servent = "You follow orders strictly. Output the answer without any additional information."

    def prep_task_spcefics(self):
        pass

    def _parse_task_name(self):
        full_task = getattr(self.args, "task", "arithmetic")
        parts = full_task.split(":")
        task_name = parts[0]
        div = parts[1] if len(parts) > 1 else None
        return task_name, div

    def _fallback_cot(self, query):
        if self._cot_helper is None:
            self._cot_helper = ChainofThought(self.args, self.task_loader)
            self._cot_helper.prep_const_prompt()
            self._cot_helper.prep_task_spcefics()
            logger.info("[tot] Tree-of-Thought not available or task unsupported; fallback to Chain-of-Thought.")
        return self._cot_helper.solve_query(query)

    def solve_query(self, query):
        start_time = time.time()
        task_name, div = self._parse_task_name()

        if task_name in ("sorting", "keyword", "set_intersection"):
            try:
                if task_name == "sorting":
                    result = self._run_sorting_tot(query)
                elif task_name == "keyword":
                    result = self._run_keyword_tot(query)
                else:  # set_intersection
                    result = self._run_set_intersection_tot(query)

                if result is None:
                    logger.warning(f"[tot] custom ToT returned None for task={task_name}, fallback to CoT.")
                    result = self._fallback_cot(query)

            except Exception as e:
                logger.warning(f"[tot] custom ToT execution failed ({e}), fallback to CoT.")
                result = self._fallback_cot(query)

        elif task_name in ("arithmetic", "large_digit"):
            try:
                if task_name == "arithmetic":
                    result = self._run_arithmetic_tot(query)
                else:  # large_digit
                    result = self._run_large_digit_tot(query)

                if result is None:
                    logger.warning(f"[tot] GoT returned None for task={task_name}, fallback to CoT.")
                    result = self._fallback_cot(query)

            except Exception as e:
                logger.warning(f"[tot] GoT execution failed ({e}), fallback to CoT.")
                result = self._fallback_cot(query)

        else:
            logger.info(f"[tot] Tree-of-Thought not available for task={task_name}; use CoT instead.")
            result = self._fallback_cot(query)

        end_time = time.time()
        self.total_runtimes.append(end_time - start_time)

        return result

    def _patch_lm_for_timing(self, lm):
        original_chat = lm.chat

        def timed_chat(*args, **kwargs):
            step_start = time.time()
            out = original_chat(*args, **kwargs)
            step_end = time.time()
            self.perstep_runtimes.append(step_end - step_start)
            return out

        lm.chat = timed_chat
        return lm

        # ---------- ToT for sorting ----------
    def _run_sorting_tot(self, query: str):
        gen_prompt = (
            "You are solving a sorting problem.\n"
            "You must sort the given list of integers in ascending order.\n"
            "Question: " + str(query) + "\n\n"
            "Generate 3 different candidate sorted results.\n"
            "Use exactly this format and nothing else:\n"
            "CANDIDATE 1: {a_1, a_2, ..., a_n}\n"
            "CANDIDATE 2: {b_1, b_2, ..., b_n}\n"
            "CANDIDATE 3: {c_1, c_2, ..., c_n}\n"
            "No explanations."
        )
        raw = self.llm_answer(gen_prompt)

        candidates = []
        for m in re.finditer(r"\{([^}]*)\}", raw):
            seq_str = m.group(1)
            nums = []
            for t in seq_str.split(","):
                t = t.strip()
                if not t:
                    continue
                try:
                    nums.append(int(t))
                except ValueError:
                    pass
            if nums:
                candidates.append(nums)

        if not candidates:
            logger.warning("[tot] _run_sorting_tot: no candidates parsed, fallback to CoT.")
            return self._fallback_cot(query)

        best_seq = None
        best_score = -1.0
        for seq in candidates:
            eval_prompt = (
                "We are checking a candidate answer for a sorting task.\n"
                f"Original question: {query}\n"
                f"Candidate answer: {seq}\n\n"
                "Evaluate this candidate on two criteria:\n"
                "1) Is it in non-decreasing order (sorted ascending)?\n"
                "2) Does it contain exactly the same multiset of integers as the original list (no missing or extra numbers)?\n\n"
                "Give a single numeric score between 0 and 1 in the format:\n"
                "SCORE: x.x\n"
                "Do not output anything else."
            )
            resp = self.llm_answer(eval_prompt)
            m = re.search(r"([01](?:\.\d+)?)", resp)
            try:
                score = float(m.group(1)) if m else 0.0
            except Exception:
                score = 0.0

            if score > best_score:
                best_score = score
                best_seq = seq

        if best_seq is None:
            logger.warning("[tot] _run_sorting_tot: all candidates scored 0, fallback to CoT.")
            return self._fallback_cot(query)

        result_str = "{" + ", ".join(str(x) for x in best_seq) + "}"
        return result_str
    
        # ---------- ToT for keyword (country extraction) ----------
    def _run_keyword_tot(self, query: str):
        gen_prompt = (
            "You are extracting country names (no continents) from the following paragraph.\n"
            "Country names should appear in the order they appear in the text, duplicates allowed.\n"
            "Paragraph:\n"
            f"{query}\n\n"
            "Generate 3 different candidate lists of countries.\n"
            "Use exactly this format and nothing else:\n"
            "CANDIDATE 1: [Country1, Country2, ...]\n"
            "CANDIDATE 2: [Country1, Country2, ...]\n"
            "CANDIDATE 3: [Country1, Country2, ...]\n"
            "No explanations."
        )
        raw = self.llm_answer(gen_prompt)

        cand_lists = []
        for m in re.finditer(r"\[([^\]]*)\]", raw):
            inner = m.group(1)
            items = []
            for t in inner.split(","):
                name = t.strip()
                if name:
                    name = name.strip('"').strip("'")
                    items.append(name)
            if items:
                cand_lists.append(items)

        if not cand_lists:
            logger.warning("[tot] _run_keyword_tot: no candidates parsed, fallback to CoT.")
            return self._fallback_cot(query)

        best_list = None
        best_score = -1.0

        for lst in cand_lists:
            eval_prompt = (
                "We are checking a candidate list of country names extracted from a paragraph.\n"
                f"Paragraph:\n{query}\n\n"
                f"Candidate list: {lst}\n\n"
                "Evaluate the candidate based on:\n"
                "1) Includes all country names that appear in the paragraph.\n"
                "2) Does not include entities that are not countries (e.g., cities, continents).\n"
                "3) Preserves the original appearance order and allows duplicates.\n\n"
                "Give a score between 0 and 1, format:\n"
                "SCORE: x.x\n"
                "No extra text."
            )
            resp = self.llm_answer(eval_prompt)
            m = re.search(r"([01](?:\.\d+)?)", resp)
            try:
                score = float(m.group(1)) if m else 0.0
            except Exception:
                score = 0.0

            if score > best_score:
                best_score = score
                best_list = lst

        if best_list is None:
            logger.warning("[tot] _run_keyword_tot: all candidates scored 0, fallback to CoT.")
            return self._fallback_cot(query)

        result_str = "[" + ", ".join(best_list) + "]"
        return result_str
    
        # ---------- ToT for set_intersection ----------
    def _run_set_intersection_tot(self, query: str):
        gen_prompt = (
            "You are solving a set intersection problem.\n"
            "The question describes two sets of integers; you must find their intersection and output it as a sorted set.\n"
            "Question: " + str(query) + "\n\n"
            "Generate 3 different candidate intersection sets.\n"
            "Use exactly this format and nothing else:\n"
            "CANDIDATE 1: {a_1, a_2, ..., a_k}\n"
            "CANDIDATE 2: {b_1, b_2, ..., b_k}\n"
            "CANDIDATE 3: {c_1, c_2, ..., c_k}\n"
            "No explanations."
        )
        raw = self.llm_answer(gen_prompt)

        candidates = []
        for m in re.finditer(r"\{([^}]*)\}", raw):
            seq_str = m.group(1)
            nums = []
            for t in seq_str.split(","):
                t = t.strip()
                if not t:
                    continue
                try:
                    nums.append(int(t))
                except ValueError:
                    pass
            if nums:
                candidates.append(nums)

        if not candidates:
            logger.warning("[tot] _run_set_intersection_tot: no candidates parsed, fallback to CoT.")
            return self._fallback_cot(query)

        best_seq = None
        best_score = -1.0
        for seq in candidates:
            eval_prompt = (
                "We are checking a candidate answer for a set intersection task.\n"
                f"Original question: {query}\n"
                f"Candidate intersection (as a sorted list): {seq}\n\n"
                "Evaluate this candidate based on:\n"
                "1) Every number in the candidate must appear in BOTH original sets.\n"
                "2) The candidate must not miss any numbers that appear in both sets.\n"
                "3) The candidate list must be sorted in non-decreasing order.\n\n"
                "Give a score between 0 and 1 in the format:\n"
                "SCORE: x.x\n"
                "No extra text."
            )
            resp = self.llm_answer(eval_prompt)
            m = re.search(r"([01](?:\.\d+)?)", resp)
            try:
                score = float(m.group(1)) if m else 0.0
            except Exception:
                score = 0.0

            if score > best_score:
                best_score = score
                best_seq = seq

        if best_seq is None:
            logger.warning("[tot] _run_set_intersection_tot: all candidates scored 0, fallback to CoT.")
            return self._fallback_cot(query)

        result_str = "{" + ", ".join(str(x) for x in best_seq) + "}"
        return result_str


# ---------- ToT for arithmetic ----------
    def _run_arithmetic_tot(self, query: str):
        """Tree of Thoughts for arithmetic task"""
        # Step 1: Generate 3 candidate solutions
        gen_prompt = (
            "You are solving an arithmetic expression.\n"
            f"Expression: {query}\n\n"
            "Follow order of operations (multiplication/division before addition/subtraction).\n"
            "Generate 3 different step-by-step solutions.\n"
            "Use exactly this format and nothing else:\n"
            "CANDIDATE 1:\n"
            "[your step-by-step calculation]\n"
            "Final answer: X\n\n"
            "CANDIDATE 2:\n"
            "[your step-by-step calculation]\n"
            "Final answer: Y\n\n"
            "CANDIDATE 3:\n"
            "[your step-by-step calculation]\n"
            "Final answer: Z\n\n"
            "No extra explanations."
        )
        raw = self.llm_answer(gen_prompt)
        
        # Step 2: Parse candidates
        candidates = []
        for match in re.finditer(r"Final answer:\s*([+-]?\d+\.?\d*)", raw, re.IGNORECASE):
            try:
                num = float(match.group(1))
                candidates.append(num)
            except ValueError:
                pass
        
        if not candidates:
            logger.warning("[tot] _run_arithmetic_tot: no candidates parsed, fallback to CoT.")
            return self._fallback_cot(query)
        
        # Step 3: Evaluate each candidate
        best_answer = None
        best_score = -1.0
        
        for answer in candidates:
            eval_prompt = (
                f"Verify this arithmetic calculation:\n"
                f"Expression: {query}\n"
                f"Candidate answer: {answer}\n\n"
                "Check:\n"
                "1) Did the calculation follow the correct order of operations?\n"
                "2) Are all intermediate steps correct?\n"
                "3) Is the final answer correct?\n\n"
                "Give a score between 0 and 1:\n"
                "SCORE: x.x\n"
                "No extra text."
            )
            resp = self.llm_answer(eval_prompt)
            
            m = re.search(r"([01](?:\.\d+)?)", resp)
            try:
                score = float(m.group(1)) if m else 0.0
            except Exception:
                score = 0.0
            
            if score > best_score:
                best_score = score
                best_answer = answer
        
        if best_answer is None:
            logger.warning("[tot] _run_arithmetic_tot: all candidates scored 0, fallback to CoT.")
            return self._fallback_cot(query)
        
        # Format output
        result_str = str(best_answer)
        # For arithmetic, keep 2 decimal places if it's a float
        if '.' in result_str and result_str != str(int(float(result_str))):
            result_str = f"{best_answer:.2f}"
        
        return result_str

# ---------- ToT for large_digit ----------
    def _run_large_digit_tot(self, query: str):
        """Tree of Thoughts for large digit addition"""
        # Step 1: Generate 3 candidate solutions
        gen_prompt = (
            "You are adding two very large integers.\n"
            f"Problem: {query}\n\n"
            "Add them digit by digit from right to left, handling carries.\n"
            "Generate 3 different solutions showing your work.\n"
            "Use exactly this format and nothing else:\n"
            "CANDIDATE 1:\n"
            "[show digit-by-digit addition with carries]\n"
            "Final sum: XXXXX\n\n"
            "CANDIDATE 2:\n"
            "[show digit-by-digit addition with carries]\n"
            "Final sum: YYYYY\n\n"
            "CANDIDATE 3:\n"
            "[show digit-by-digit addition with carries]\n"
            "Final sum: ZZZZZ\n\n"
            "No extra explanations."
        )
        raw = self.llm_answer(gen_prompt)
        
        # Step 2: Parse candidates
        candidates = []
        for match in re.finditer(r"Final sum:\s*(\d+)", raw, re.IGNORECASE):
            try:
                num = int(match.group(1))
                candidates.append(num)
            except ValueError:
                pass
        
        if not candidates:
            logger.warning("[tot] _run_large_digit_tot: no candidates parsed, fallback to CoT.")
            return self._fallback_cot(query)
        
        # Step 3: Evaluate each candidate
        best_answer = None
        best_score = -1.0
        
        for answer in candidates:
            eval_prompt = (
                f"Verify this large number addition:\n"
                f"Problem: {query}\n"
                f"Candidate answer: {answer}\n\n"
                "Check:\n"
                "1) Were carries handled correctly at each digit position?\n"
                "2) Is the number of digits in the result correct?\n"
                "3) Is the final sum mathematically correct?\n\n"
                "Give a score between 0 and 1:\n"
                "SCORE: x.x\n"
                "No extra text."
            )
            resp = self.llm_answer(eval_prompt)
            
            m = re.search(r"([01](?:\.\d+)?)", resp)
            try:
                score = float(m.group(1)) if m else 0.0
            except Exception:
                score = 0.0
            
            if score > best_score:
                best_score = score
                best_answer = answer
        
        if best_answer is None:
            logger.warning("[tot] _run_large_digit_tot: all candidates scored 0, fallback to CoT.")
            return self._fallback_cot(query)
        
        return str(best_answer)
