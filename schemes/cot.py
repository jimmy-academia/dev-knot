import logging
from .base import BaseScheme

Task_Specific_Example = {
    "gsm_symbolic":"""
Question: There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today? 

Let's think step by step 

1. **Understand the given information:**
   - Initially, there are 15 trees in the grove.
   - After planting more trees, there will be a total of 21 trees.

2. **Determine the change in the number of trees:**
   - The grove workers planted additional trees to reach the total of 21.
   - To find out how many trees were planted, subtract the initial number of trees from the final total.

3. **Perform the calculation:**
   \[
   \text{Number of trees planted} = \text{Final total} - \text{Initial total}
   \]
   \[
   \text{Number of trees planted} = 21 - 15
   \]
   \[
   \text{Number of trees planted} = 6
   \]

4. **Answer:**
   The grove workers planted **6 trees** today.

Question: %s


      """
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
    
