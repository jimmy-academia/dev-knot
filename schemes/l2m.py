import logging
from .base import BaseScheme
from .prompt_generator import generate_large_digit_prompt, generate_arithmetic_prompt, \
                              generate_set_intersection_prompt, generate_sorting_prompt, \
                              generate_keyword_counting_prompt, generate_yelp_prompt

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

keyword_counting_subquestions = [
    "Identify the country names from the first portion of the text.",
    "Identify the country names from the next portion of the text.",
    "Continue identifying the country names from the next section.",
    "List any remaining country names from the final portion of the text.",
    "What is the final list of country names extracted?"
]

yelp_subquestions = ['Count the number of positive reviews in the first chunk',
                     'Count the number of positive reviews in the second chunk',
                     'Count the number of positive reviews in the third chunk',
                     'Count the number of positive reviews in the last chunk',
                     'Summarize the total number of positive reviews at the end.']

subquestion_dict = {'large_digit':{'8':large_digit_8_subquestions,'16':large_digit_16_subquestions,'32':large_digit_32_subquestions},
                    'all_arith':{'08':all_arith_subquestions,'16':all_arith_subquestions,'32':all_arith_subquestions},
                    'set_intersection':{'032':set_intersection_32_subquestions, '064':set_intersection_64_subquestions, '128':set_intersection_128_subquestions},
                    'sorting':{'016':sorting_subquestions,'032':sorting_subquestions,'064':sorting_subquestions},
                    'keyword_counting':keyword_counting_subquestions,
                    'yelp':yelp_subquestions}                       

def get_text_chunks(text):
    chunks = [
                text[:400],  # First chunk
                text[400:800],  # Second chunk
                text[800:1200],  # Third chunk
                text[1200:]  # Last chunk
             ]
    return chunks

def get_review_chunks(reviews):
    chunks = [
                (reviews[:2]),  # First chunk
                (reviews[2:4]),  # Second chunk
                (reviews[4:6]),  # Third chunk
                (reviews[6:])  # Last chunk
             ]
    return chunks

class Least2Most(BaseScheme):    
    def prep_const_prompt(self):
        pass

    def prep_task_spcefics(self):
        if self.args.div:
            self.ltm_subquestions = subquestion_dict.get(self.args.task).get(self.args.div)
        else:
            self.ltm_subquestions = subquestion_dict.get(self.args.task)
        # self.ltm_solving_example = Task_Specific_Example.get(self.args.task).get('solving')
    
    def generate_prompt(self, question, context, text=None):
        if self.args.task == 'large_digit':
            prompt = generate_large_digit_prompt(question, context)
        if self.args.task == 'all_arith':
            prompt = generate_arithmetic_prompt(question, context)
        if self.args.task == 'set_intersection':
            prompt = generate_set_intersection_prompt(question, context)
        if self.args.task == 'sorting':
            prompt = generate_sorting_prompt(question, context)
        if self.args.task == 'keyword_counting':
            prompt = generate_keyword_counting_prompt(question, context, text)
        if self.args.task == 'yelp':
            prompt = generate_yelp_prompt(question, context, text)
        return prompt
    
    def solve_query(self, query):
        context = f'{query}'
        for i, question in enumerate(self.ltm_subquestions):
            if self.args.task == 'keyword_counting':
                text_chunks = get_text_chunks(query)
                if i != len(self.ltm_subquestions)-1:
                    prompt = self.generate_prompt(question, context, text_chunks[i])
                else:
                    prompt = self.generate_prompt(question, context)
            elif self.args.task == 'yelp':
                review_chunk = get_review_chunks(query)
                if i != len(self.ltm_subquestions)-1:
                    prompt = self.generate_prompt(question, context, review_chunk[i])
                else:
                    prompt = self.generate_prompt(question, context)
            else:
                prompt = self.generate_prompt(question, context)
            answer = self.llm_answer(prompt)
            print(f"Step {i} - Q: {question}\nA: {answer}\n")
            context += f"\n{question}\n{answer}"
        if self.args.task == 'large_digit' or self.args.task == 'all_arith' or self.args.task == 'yelp':
            output = self.llm_answer("extract the numerical of the answer:"+answer)
        elif self.args.task == 'set_intersection':
            # answer = answer.split(', ')
            # output = [int(o) for o in answer]
            output = self.llm_answer(f"extract the set form of the answer:{answer}")
        elif self.args.task == 'sorting' or self.args.task == 'keyword_counting':
            output = self.llm_answer(f"extract the list form of the answer:{answer}")
        
        logging.info(f'>>>>>>>>>>>> final result: {output} <<<<<<<<<<<<<')
        return output