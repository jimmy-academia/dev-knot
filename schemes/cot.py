import logging
from .base import BaseScheme

Task_Specific_Example = {

}

class ChainofThought(BaseScheme):
    
    def prep_const_prompt(self):
        self.cot_prompt = "Let's think step by step"

    def prep_task_spcefics(self):
        self.cot_example = Task_Specific_Example.get(self.args.task)

    def solve_query(self, query):
        output = self.llm_answer(self.cot_example%query +self.cot_prompt)
        output = self.llm_answer("extract the numerical of the answer:"+output)
        logging.info(f'>>>>>>>>>>>> final result: {output} <<<<<<<<<<<<<')
        return output
    
class ZeroCoT(BaseScheme):
    
    def prep_const_prompt(self):
        pass

    def prep_task_spcefics(self):
        pass

    def solve_query(self, query):
        output = self.llm_answer(query + "\nLet's think step by step")
        output = self.llm_answer("extract the numerical of the answer:"+output)
        logging.info(f'>>>>>>>>>>>> final result: {output} <<<<<<<<<<<<<')
        return output
    
