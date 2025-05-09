import logging
import json
from .base import BaseScheme
from utils import readf
from .aot_module import AoT

logger = logging.getLogger(__name__)

class AlgorithmofThought(BaseScheme):    
    def prep_const_prompt(self):
        if self.args.task == 'large_digit':
            prompt = 'We are solving an addition problem of large-digit numbers: '
        if self.args.task == 'all_arith':
            prompt = 'We are solving arithmetic problems: '
        if self.args.task == 'set_intersection': 
            prompt = 'We are find the intersection of sets: '
        if self.args.task == 'sorting':
            prompt = 'We are sorting a list of numbers: '
        if self.args.task == 'keyword_counting':
            prompt = 'We are extracting the names of countries occurred in the paragraph: '
        if self.args.task == 'yelp':
            prompt = 'We are counting the number of positive reviews from the review list: '
        return prompt

    def prep_task_spcefics(self):
        pass

    def solve_query(self, query):
        init_prompt = self.prep_const_prompt() + query
        dfs = AoT(num_thoughts=10, max_steps=20, value_threshold=1,
                  initial_prompt=init_prompt, openai_api_key=readf('.openaiapi_key'))
        result = dfs.solve()
        output = self.llm_answer("extract the numerical of the answer:"+result)
        logging.info(f'>>>>>>>>>>>> final result: {output} <<<<<<<<<<<<<')
        return output