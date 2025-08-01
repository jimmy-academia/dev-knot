import logging
from .base import BaseScheme

reasoning_modules = [
    "1. How could I devise an experiment to help solve that problem?",
    "2. Make a list of ideas for solving this problem, and apply them one by one to the problem to see if any progress can be made.",
    #"3. How could I measure progress on this problem?",
    "4. How can I simplify the problem so that it is easier to solve?",
    "5. What are the key assumptions underlying this problem?",
    "6. What are the potential risks and drawbacks of each solution?",
    "7. What are the alternative perspectives or viewpoints on this problem?",
    "8. What are the long-term implications of this problem and its solutions?",
    "9. How can I break down this problem into smaller, more manageable parts?",
    "10. Critical Thinking: This style involves analyzing the problem from different perspectives, questioning assumptions, and evaluating the evidence or information available. It focuses on logical reasoning, evidence-based decision-making, and identifying potential biases or flaws in thinking.",
    "11. Try creative thinking, generate innovative and out-of-the-box ideas to solve the problem. Explore unconventional solutions, thinking beyond traditional boundaries, and encouraging imagination and originality.",
    #"12. Seek input and collaboration from others to solve the problem. Emphasize teamwork, open communication, and leveraging the diverse perspectives and expertise of a group to come up with effective solutions.",
    "13. Use systems thinking: Consider the problem as part of a larger system and understanding the interconnectedness of various elements. Focuses on identifying the underlying causes, feedback loops, and interdependencies that influence the problem, and developing holistic solutions that address the system as a whole.",
    "14. Use Risk Analysis: Evaluate potential risks, uncertainties, and tradeoffs associated with different solutions or approaches to a problem. Emphasize assessing the potential consequences and likelihood of success or failure, and making informed decisions based on a balanced analysis of risks and benefits.",
    #"15. Use Reflective Thinking: Step back from the problem, take the time for introspection and self-reflection. Examine personal biases, assumptions, and mental models that may influence problem-solving, and being open to learning from past experiences to improve future approaches.",
    "16. What is the core issue or problem that needs to be addressed?",
    "17. What are the underlying causes or factors contributing to the problem?",
    "18. Are there any potential solutions or strategies that have been tried before? If yes, what were the outcomes and lessons learned?",
    "19. What are the potential obstacles or challenges that might arise in solving this problem?",
    "20. Are there any relevant data or information that can provide insights into the problem? If yes, what data sources are available, and how can they be analyzed?",
    "21. Are there any stakeholders or individuals who are directly affected by the problem? What are their perspectives and needs?",
    "22. What resources (financial, human, technological, etc.) are needed to tackle the problem effectively?",
    "23. How can progress or success in solving the problem be measured or evaluated?",
    "24. What indicators or metrics can be used?",
    "25. Is the problem a technical or practical one that requires a specific expertise or skill set? Or is it more of a conceptual or theoretical problem?",
    "26. Does the problem involve a physical constraint, such as limited resources, infrastructure, or space?",
    "27. Is the problem related to human behavior, such as a social, cultural, or psychological issue?",
    "28. Does the problem involve decision-making or planning, where choices need to be made under uncertainty or with competing objectives?",
    "29. Is the problem an analytical one that requires data analysis, modeling, or optimization techniques?",
    "30. Is the problem a design challenge that requires creative solutions and innovation?",
    "31. Does the problem require addressing systemic or structural issues rather than just individual instances?",
    "32. Is the problem time-sensitive or urgent, requiring immediate attention and action?",
    "33. What kinds of solution typically are produced for this kind of problem specification?",
    "34. Given the problem specification and the current best solution, have a guess about other possible solutions."
    "35. Let’s imagine the current best solution is totally wrong, what other ways are there to think about the problem specification?"
    "36. What is the best way to modify this current best solution, given what you know about these kinds of problem specification?"
    "37. Ignoring the current best solution, create an entirely new solution to the problem."
    #"38. Let’s think step by step."
    "39. Let’s make a step by step plan and implement it with good notation and explanation."
]

# task_example = "Lisa has 10 apples. She gives 3 apples to her friend and then buys 5 more apples from the store. How many apples does Lisa have now?"



class Selfdiscover(BaseScheme):    
    def prep_const_prompt(self):
        if self.args.task == 'large_digit':
            prompt = 'We are solving an addition problem of large-digit numbers: '
        if self.args.task == 'all_arith':
            prompt = 'We are solving arithmetic problems: '
        if self.args.task == 'set_intersection': 
            prompt = 'We are find the intersection of sets: '
        if self.args.task == 'sorting':
            prompt = 'We are sorting a list of numbers: '
        if self.args.task == 'keyword':
            prompt = 'We are extracting every occurrence of country names, preserving duplicates and maintaining their original order in the paragraph: '
        if self.args.task == 'yelp':
            prompt = 'We are counting the number of positive reviews from the review list: '
        return prompt
    
    def prep_task_spcefics(self):
        pass
    
    # STAGE 1
    def select_reasoning_modules(self, task_description, reasoning_modules):
        """
        Step 1: SELECT relevant reasoning modules for the task.
        """
        prompt = f"Given the task: {task_description}, which of the following reasoning modules are relevant? Do not elaborate on why.\n\n" + "\n".join(reasoning_modules)
        selected_modules = self.llm_answer(prompt)
        return selected_modules

    def adapt_reasoning_modules(self, selected_modules, task_example):
        """
        Step 2: ADAPT the selected reasoning modules to be more specific to the task.
        """
        prompt = f"Without working out the full solution, adapt the following reasoning modules to be specific to our task:\n{selected_modules}\n\nOur task:\n{task_example}"
        adapted_modules = self.llm_answer(prompt)
        return adapted_modules

    def implement_reasoning_structure(self, adapted_modules, task_description):
        """
        Step 3: IMPLEMENT the adapted reasoning modules into an actionable reasoning structure.
        """
        prompt = f"Without working out the full solution, create an actionable reasoning structure for the task using these adapted reasoning modules:\n{adapted_modules}\n\nTask Description:\n{task_description}"
        reasoning_structure = self.llm_answer(prompt)
        return reasoning_structure

    # STAGE 2

    def execute_reasoning_structure(self, reasoning_structure, task_instance):
        """
        Execute the reasoning structure to solve a specific task instance.
        """
        prompt = f"Using the following reasoning structure: {reasoning_structure}\n\nSolve this task, providing your final answer: {task_instance}"
        solution = self.llm_answer(prompt)
        return solution
    
    def solve_query(self, query):
        task_example = self.prep_const_prompt() + query
        selected_modules = self.select_reasoning_modules(task_example, reasoning_modules)
        adapted_modules = self.adapt_reasoning_modules(selected_modules, task_example)
        reasoning_structure = self.implement_reasoning_structure(adapted_modules, task_example)
        answer = self.execute_reasoning_structure(reasoning_structure, task_example)
        if self.args.task == 'large_digit' or self.args.task == 'all_arith' or self.args.task == 'yelp':
            output = self.llm_answer("extract the numerical of the answer from: "+answer+" Only output a number.")
        elif self.args.task == 'set_intersection':
            # answer = answer.split(', ')
            # output = [int(o) for o in answer]
            output = self.llm_answer(f"extract the set form of the answer:{answer}")
        elif self.args.task == 'sorting' or self.args.task == 'keyword':
            output = self.llm_answer(f"extract the Python list form of the answer:{answer}")
        return output