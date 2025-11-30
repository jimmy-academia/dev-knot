from typing import Dict, List, Union
from graph_of_thoughts import operations, prompter, parser

class ArithmeticPrompter(prompter.Prompter):
    """Arithmetic prompter"""
    
    arith_prompt = """<Instruction> Calculate the result of the arithmetic expression. Output only the final numeric result. </Instruction>

<Examples>
Input: 3+5*2-4
Output: 9

Input: 8/2+3*4
Output: 16
</Examples>

Input: {input}
Output:"""
    
    def aggregation_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        return self.arith_prompt.format(input=state_dicts[0]['original'])
    
    def generate_prompt(self, num_branches: int, **kwargs) -> str:
        state = kwargs.get('state', kwargs)
        return self.arith_prompt.format(input=state['original'])
    
    def improve_prompt(self, **kwargs) -> str:
        return "Recalculate the arithmetic expression."
    
    def validation_prompt(self, **kwargs) -> str:
        return "Is the calculation correct? Answer 'Yes' or 'No'."
    
    def score_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        return "Rate correctness from 0 to 1."

class ArithmeticParser(parser.Parser):
    """Arithmetic parser"""
    
    def __init__(self):
        self.cache = {}
    
    def parse_aggregation_answer(
        self, states: List[Dict], texts: List[str]
    ) -> Union[Dict, List[Dict]]:
        new_states = []
        for text in texts:
            try:
                import re
                numbers = re.findall(r'-?\d+\.?\d*', text)
                result = float(numbers[0]) if numbers else 0.0
            except:
                result = 0.0
            
            new_state = states[0].copy()
            new_state["current"] = result
            new_state["phase"] = states[0]["phase"] + 1
            new_states.append(new_state)
        
        return new_states[0] if len(new_states) == 1 else new_states
    
    def parse_generate_answer(self, state: Dict, texts: List[str]) -> List[Dict]:
        import re
        
        new_states = []
        for text in texts:
            try:
                numbers = re.findall(r'-?\d+\.?\d*', text)
                result = float(numbers[0]) if numbers else 0.0
            except:
                result = 0.0
            
            new_state = state.copy()
            new_state["current"] = result
            new_state["phase"] = state["phase"] + 1
            new_states.append(new_state)
        
        return new_states
    
    def parse_improve_answer(self, state: Dict, texts: List[str]) -> Dict:
        import re
        
        text = texts[0] if texts else "0"
        try:
            numbers = re.findall(r'-?\d+\.?\d*', text)
            result = float(numbers[0]) if numbers else 0.0
        except:
            result = 0.0
        
        new_state = state.copy()
        new_state["current"] = result
        return new_state
    
    def parse_validation_answer(self, state: Dict, texts: List[str]) -> bool:
        text = texts[0] if texts else ""
        return "yes" in text.lower()
    
    def parse_score_answer(self, states: List[Dict], texts: List[str]) -> List[float]:
        scores = []
        for text in texts:
            try:
                score = float(text.strip())
                scores.append(score)
            except:
                scores.append(0.0)
        
        if len(scores) == 1 and len(states) > 1:
            scores = scores * len(states)
        
        return scores

def got():
    graph = operations.GraphOfOperations()
    graph.append_operation(operations.Generate(1, 1))
    graph.append_operation(operations.Aggregate(1))
    return graph

def get_prompter():
    return ArithmeticPrompter()

def get_parser():
    return ArithmeticParser()