from typing import Dict, List, Union
from graph_of_thoughts import operations, prompter, parser

class SortingPrompter(prompter.Prompter):
    """Sorting prompter"""
    
    sort_prompt = """<Instruction> Sort the following list of numbers in ascending order. Output only the sorted list of numbers, no additional text. </Instruction>

<Examples>
Input: [5, 1, 0, 1, 2, 0, 4, 8, 1, 9, 5, 1, 3, 3, 9, 7]
Output: [0, 0, 1, 1, 1, 1, 2, 3, 3, 4, 5, 5, 7, 8, 9, 9]
</Examples>

Input: {input}
Output:"""
    
    def aggregation_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        return self.sort_prompt.format(input=state_dicts[0]['original'])
    
    def generate_prompt(self, num_branches: int, **kwargs) -> str:
        state = kwargs.get('state', kwargs)
        return self.sort_prompt.format(input=state['original'])
    
    def improve_prompt(self, **kwargs) -> str:
        current = kwargs.get('current', '')
        original = kwargs.get('original', '')
        return f"""Fix the incorrectly sorted list: {current}
Original: {original}
Output only the corrected sorted list."""
    
    def validation_prompt(self, **kwargs) -> str:
        return "Is this list correctly sorted? Answer 'Yes' or 'No'."
    
    def score_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        return "Rate correctness from 0 to 1."

class SortingParser(parser.Parser):
    """Sorting parser"""
    
    def __init__(self):
        self.cache = {}
    
    def parse_aggregation_answer(
        self, states: List[Dict], texts: List[str]
    ) -> Union[Dict, List[Dict]]:
        import ast
        
        new_states = []
        for text in texts:
            try:
                result = ast.literal_eval(text.strip())
                if isinstance(result, list):
                    result = sorted(result)
                else:
                    result = []
            except:
                result = []
            
            new_state = states[0].copy()
            new_state["current"] = result
            new_state["phase"] = states[0]["phase"] + 1
            new_states.append(new_state)
        
        return new_states[0] if len(new_states) == 1 else new_states
    
    def parse_generate_answer(self, state: Dict, texts: List[str]) -> List[Dict]:
        import ast
        
        new_states = []
        for text in texts:
            try:
                result = ast.literal_eval(text.strip())
                if not isinstance(result, list):
                    result = []
            except:
                result = []
            
            new_state = state.copy()
            new_state["current"] = result
            new_state["phase"] = state["phase"] + 1
            new_states.append(new_state)
        
        return new_states
    
    def parse_improve_answer(self, state: Dict, texts: List[str]) -> Dict:
        import ast
        
        text = texts[0] if texts else ""
        try:
            result = ast.literal_eval(text.strip())
            if not isinstance(result, list):
                result = []
        except:
            result = []
        
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
        
        # 如果只有一个分数但有多个 states，复制分数
        if len(scores) == 1 and len(states) > 1:
            scores = scores * len(states)
        
        return scores

def got() -> operations.GraphOfOperations:
    graph = operations.GraphOfOperations()
    graph.append_operation(operations.Generate(1, 1))
    graph.append_operation(operations.Aggregate(1))
    return graph

def get_prompter():
    return SortingPrompter()

def get_parser():
    return SortingParser()