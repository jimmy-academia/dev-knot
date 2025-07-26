import re
import logging
import math
# Assuming BaseScheme and prompt generators are in the correct relative path
from .base import BaseScheme
from .prompt_generator import generate_large_digit_prompt, generate_arithmetic_prompt, \
                              generate_set_intersection_prompt, generate_sorting_prompt, \
                              generate_keyword_counting_prompt, generate_yelp_prompt

# --- Subquestion Definitions ---
# (Keep the subquestion definitions as they were in the previous correct version)

large_digit_8_subquestions = ['Add the rightmost 4 digits (with carry)',
                              'Add the next 4 digits (with carry).',
                              'Add the leftmost digits if there is any carry in the previous step. If not, please report the leftmost digit.',
                              'What is the final sum after applying all carries?']

large_digit_16_subquestions = ['Add the rightmost 8 digits (with carry)',
                               'Add the next 8 digits (with carry).',
                               'Add the leftmost digits if there is any carry in the previous step. If not, please report the leftmost digit.',
                               'What is the final sum after applying all carries?']

large_digit_32_subquestions = ['Add the rightmost 16 digits (with carry)',
                               'Add the next 16 digits (with carry).',
                               'Add the leftmost digits if there is any carry in the previous step. If not, please report the leftmost digit.',
                               'What is the final sum after applying all carries?']

all_arith_subquestions = ['Compute multiplication and division first.',
                          'Then compute the addition and subtraction.',
                          'Round the sum to two decimal places.']

set_intersection_32_subquestions = ["Check the first 16 elements of both sets and list common elements.",
                                    "Check the remaining 16 elements of both sets and list common elements.",
                                    "What is the final intersection of the two sets?"]

set_intersection_64_subquestions = ["Check the first 32 elements of both sets and list common elements.",
                                    "Check the remaining 32 elements of both sets and list common elements.",
                                    "What is the final intersection of the two sets?"]

set_intersection_128_subquestions = ["Check the first 64 elements of both sets and list common elements.",
                                     "Check the remaining 64 elements of both sets and list common elements.",
                                     "What is the final intersection of the two sets?"]

sorting_subquestions = ['Split the list into two equal halves.',
                        'Convert each element in each part to an integer and sort each part in ascending order.',
                        'Merge the sorted lists into a single sorted list.']

# Generic subquestions for keyword counting, assuming 4 processing steps + 1 summary
keyword_counting_subquestions_base = [
    "Carefully Extract all country names (no continents) in the order of their appearance from the following portion of the text (repeated is allowed).",
    "Carefully Extract all country names (no continents) in the order of their appearance from the next portion of the text (repeated is allowed).",
    "Carefully Extract all country names (no continents) in the order of their appearance from the next portion of the text (repeated is allowed).",
    "Carefully Extract all country names (no continents) in the order of their appearance from the final portion of the text (repeated is allowed).",
    "Combine the list. What is the final list of country names extracted? Output in a list format such as [Country_name, Country_name, ... Country_name]."
]

# Generic subquestions for yelp, assuming 4 processing steps + 1 summary
yelp_subquestions_base = ['Count the number of positive reviews in the first chunk',
                          'Count the number of positive reviews in the second chunk',
                          'Count the number of positive reviews in the third chunk',
                          'Count the number of positive reviews in the last chunk',
                          'Summarize the total number of positive reviews at the end.']


# --- Subquestion Dictionary ---
# Updated to use 'keyword' instead of 'keyword_counting'
subquestion_dict = {
    'large_digit': {
        '8': large_digit_8_subquestions,
        '16': large_digit_16_subquestions,
        '32': large_digit_32_subquestions
    },
    'all_arith': {
        '08': all_arith_subquestions,
        '16': all_arith_subquestions,
        '32': all_arith_subquestions
    },
    'set_intersection': {
        '032': set_intersection_32_subquestions,
        '064': set_intersection_64_subquestions,
        '128': set_intersection_128_subquestions
    },
    'sorting': {
        '016': sorting_subquestions,
        '032': sorting_subquestions,
        '064': sorting_subquestions
    },
    'keyword': { # Renamed from keyword_counting
        '1': keyword_counting_subquestions_base,
        '2': keyword_counting_subquestions_base,
        '4': keyword_counting_subquestions_base
    },
    'yelp': {
        '10': yelp_subquestions_base,
        '20': yelp_subquestions_base,
        '30': yelp_subquestions_base
    }
}

# --- Dynamic Chunking Functions ---
# (Keep the chunking functions as they were)

def get_text_chunks(text, num_chunks):
    """Splits text into a specified number of roughly equal chunks."""
    if not text or num_chunks <= 0:
        return []
    text_len = len(text)
    base_chunk_size = text_len // num_chunks
    remainder = text_len % num_chunks
    chunks = []
    start_index = 0
    for i in range(num_chunks):
        chunk_size = base_chunk_size + (1 if i < remainder else 0)
        end_index = start_index + chunk_size
        # Ensure end_index does not exceed text length, especially with small texts/large num_chunks
        end_index = min(end_index, text_len)
        chunks.append(text[start_index:end_index])
        start_index = end_index
        # Break if we've reached the end of the text prematurely
        if start_index >= text_len:
            break
    # Filter out empty chunks just in case
    return [chunk for chunk in chunks if chunk]



def parse_yelp_reviews(concatenated_reviews):
    """Parses concatenated Yelp-style reviews into a list of individual review strings."""
    # Split based on [REVIEW_n] markers
    pattern = r'\[REVIEW_\d+\]'
    parts = re.split(pattern, concatenated_reviews)
    # The first split is empty if text starts with [REVIEW_n], so skip it
    reviews = [part.strip() for part in parts if part.strip()]
    return reviews

def get_review_chunks(concatenated_reviews, num_chunks):
    """Parses and splits concatenated Yelp reviews into specified number of chunks."""
    reviews = parse_yelp_reviews(concatenated_reviews)
    if not reviews or num_chunks <= 0:
        return []

    num_reviews = len(reviews)
    base_chunk_size = num_reviews // num_chunks
    remainder = num_reviews % num_chunks
    chunks = []
    start_index = 0

    for i in range(num_chunks):
        chunk_size = base_chunk_size + (1 if i < remainder else 0)
        end_index = start_index + chunk_size
        end_index = min(end_index, num_reviews)
        chunks.append(reviews[start_index:end_index])
        start_index = end_index
        if start_index >= num_reviews:
            break

    return [chunk for chunk in chunks if chunk]

# --- Least2Most Scheme Class ---

class Least2Most(BaseScheme):
    def prep_const_prompt(self):
        """Placeholder for constant prompt preparation if needed."""
        pass

    def prep_task_spcefics(self):
        """Prepares task-specific attributes like subquestions based on task and division."""
        # Extract base task name if division is present (e.g., "keyword:2" -> "keyword")
        task_name = self.args.task.split(':')[0]

        task_subq_data = subquestion_dict.get(task_name)
        self.ltm_subquestions = None # Initialize

        if task_subq_data is None:
             # Task not found in subquestion_dict
             raise ValueError(f"Task '{task_name}' not defined in subquestion_dict.")

        if isinstance(task_subq_data, dict):
            # Task has divisions (like large_digit, yelp, keyword)
            if self.args.div:
                self.ltm_subquestions = task_subq_data.get(self.args.div)
                if self.ltm_subquestions is None:
                     logging.error(f"Subquestions not found for task '{task_name}' with division '{self.args.div}'")
                     # Attempt to use a default or raise error
                     default_key = next(iter(task_subq_data), None)
                     if default_key:
                         logging.warning(f"Using default subquestions for key '{default_key}'")
                         self.ltm_subquestions = task_subq_data.get(default_key)
                     else:
                          raise ValueError(f"No subquestions defined for task '{task_name}' and division '{self.args.div}', and no default found.")
            else:
                # Division expected based on dict structure but not provided
                 raise ValueError(f"Task '{task_name}' requires a division argument ('div') because it has sub-entries in subquestion_dict, but none was provided via --task task:div or --div.")
        elif isinstance(task_subq_data, list):
             # Task does not have divisions (or div not applicable like sorting)
             # Check if div was provided unnecessarily
             if self.args.div:
                 logging.warning(f"Division '{self.args.div}' provided for task '{task_name}', but this task does not use divisions in subquestion_dict. Ignoring division.")
             self.ltm_subquestions = task_subq_data
        else:
            # Should not happen if the first check passed, but as a safeguard:
            raise TypeError(f"Unexpected data type for task '{task_name}' in subquestion_dict: {type(task_subq_data)}")


        if not self.ltm_subquestions:
             # This case might occur if logic above fails or div is missing when needed
             raise ValueError(f"Could not determine subquestions for task '{task_name}' (div: {self.args.div})")

        # Use task_name here for logging consistency
        # logging.info(f"Using {len(self.ltm_subquestions)} subquestions for task '{task_name}' (div: {self.args.div})")


    def generate_prompt(self, question, context, text_chunk=None):
        """Generates the appropriate prompt based on the task."""
        # Extract base task name if division is present (e.g., "keyword:2" -> "keyword")
        task_name = self.args.task.split(':')[0]

        # Pass text_chunk only if it's relevant for the prompt generation function
        if task_name == 'large_digit':
            prompt = generate_large_digit_prompt(question, context)
        elif task_name == 'all_arith':
            prompt = generate_arithmetic_prompt(question, context)
        elif task_name == 'set_intersection':
            prompt = generate_set_intersection_prompt(question, context)
        elif task_name == 'sorting':
            prompt = generate_sorting_prompt(question, context)
        elif task_name == 'keyword': # **** UPDATED THIS LINE ****
            # Pass text_chunk if provided (for chunk-specific questions)
            prompt = generate_keyword_counting_prompt(question, context, text_chunk)
        elif task_name == 'yelp':
             # Pass text_chunk (which is a list of reviews here) if provided
            prompt = generate_yelp_prompt(question, context, text_chunk)
        else:
             # Use task_name in the error message
             raise ValueError(f"Prompt generation not defined for task: {task_name}")
        return prompt

    def solve_query(self, query):
        """Solves the query using the Least-to-Most approach with subquestions."""
        # Extract base task name if division is present (e.g., "keyword:2" -> "keyword")
        task_name = self.args.task.split(':')[0]

        context = f'{query}' # Initial context is the main query/data
        final_answer = "" # Store the answer from the last step

        # Prepare chunks beforehand if needed
        text_chunks = []
        review_chunks = []
        num_processing_steps = len(self.ltm_subquestions) - 1 # Assume last question is summary

        # Ensure num_processing_steps is not negative
        if num_processing_steps < 0:
             logging.warning("Warning: Only one subquestion found. Assuming it's the final question.")
             num_processing_steps = 0 # Or handle as error if structure requires multiple steps

        if task_name == 'keyword' and num_processing_steps > 0:
             # Expects query to be the text
             text_chunks = get_text_chunks(query, num_processing_steps)
             if len(text_chunks) != num_processing_steps:
                 logging.warning(f"Keyword Task: Expected {num_processing_steps} text chunks based on subquestions, but generated {len(text_chunks)} based on text length. Processing available chunks.")
                 # The loop below will naturally handle fewer chunks if generated
        elif task_name == 'yelp' and num_processing_steps > 0:
             # Expects query to be a list of reviews
             review_chunks = get_review_chunks(query, num_processing_steps)
             if len(review_chunks) != num_processing_steps:
                  logging.warning(f"Yelp Task: Expected {num_processing_steps} review chunks based on subquestions, but generated {len(review_chunks)} based on review count. Processing available chunks.")
                   # The loop below will naturally handle fewer chunks if generated

        # Iterate through subquestions
        for i, question in enumerate(self.ltm_subquestions):
            current_chunk = None
            is_final_question = (i == len(self.ltm_subquestions) - 1)

            # Determine the chunk based on task and step index
            if task_name == 'keyword' and not is_final_question and i < len(text_chunks):
                current_chunk = text_chunks[i]
            elif task_name == 'yelp' and not is_final_question and i < len(review_chunks):
                current_chunk = review_chunks[i]

            # Generate prompt for the current step
            # Pass the chunk only if it's relevant and not the final summary question
            prompt = self.generate_prompt(question, context, text_chunk=current_chunk) # Pass chunk regardless, let generator handle None

            # Get answer from LLM
            # Ensure self.llm_answer exists and is callable
            if not hasattr(self, 'llm_answer') or not callable(self.llm_answer):
                raise NotImplementedError("The 'llm_answer' method is not defined or not callable in the BaseScheme or Least2Most class.")
            answer = self.llm_answer(prompt)

            # print(f"Step {i} - Q: {question}\nA: {answer}\n")

            # Update context for the next step
            context += f"\n{question}\n{answer}"
            final_answer = answer # Keep track of the last answer

        # Extract final result based on task type
        output = None
        # Use task_name for checks
        if task_name in ['large_digit', 'all_arith', 'yelp']:
            # Extract numerical value from the final answer
            output = self.llm_answer(f"extract the numerical value of the answer: {final_answer}")
        elif task_name == 'set_intersection':
            # Extract set representation from the final answer
            output = self.llm_answer(f"extract the set form of the answer: {final_answer}")
        # elif task_name in ['sorting', 'keyword']: # Updated check
            # output = final_answer
             # Extract list representation from the final answer
            # output = self.llm_answer(f"extract the list form of the answer: {final_answer}")
        else:
             # Default or unknown task type - return the raw final answer
             logging.warning(f"No specific extraction logic for task '{task_name}'. Returning raw final answer.")
             output = final_answer


        # logging.info(f'>>>>>>>>>>>> final result: {output} <<<<<<<<<<<<<')
        # print(self.ground_truth)
        # input()
        return output

