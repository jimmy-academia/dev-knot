from typing import Dict, List, Union
from graph_of_thoughts import operations, prompter, parser

class IntersectionPrompter(prompter.Prompter):
    """Set intersection prompter"""
    
    intersection_prompt = """<Instruction> Find the intersection of two sets. Output only common elements as a list. </Instruction>

<Examples>
Input Set 1: [13, 16, 30, 6]
Input Set 2: [25, 24, 10, 16]
Output: [16]
</Examples>

Input Set 1: {set1}
Input Set 2: {set2}
Output:"""
    
    def aggregation_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        original = state_dicts[0]['original']
        parts = original.split(',', 1)
        if len(parts) == 2:
            return self.intersection_prompt.format(set1=parts[0].strip(), set2=parts[1].strip())
        return f"Find intersection of: {original}"
    
    def generate_prompt(self, num_branches: int, **kwargs) -> str:
        state = kwargs.get('state', kwargs)
        original = state['original']
        parts = original.split(',', 1)
        if len(parts) == 2:
            return self.intersection_prompt.format(set1=parts[0].strip(), set2=parts[1].strip())
        return f"Find intersection of: {original}"
    
    def improve_prompt(self, **kwargs) -> str:
        return "Improve the intersection result."
    
    def validation_prompt(self, **kwargs) -> str:
        return "Is correct? Answer 'Yes' or 'No'."
    
    def score_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        return "Rate from 0 to 1."

class IntersectionParser(parser.Parser):
    """Set intersection parser"""
    
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
                    result = sorted(list(set(result)))
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
        
        text = texts[0] if texts else "[]"
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
        
        if len(scores) == 1 and len(states) > 1:
            scores = scores * len(states)
        
        return scores

def got():
    graph = operations.GraphOfOperations()
    graph.append_operation(operations.Generate(1, 1))
    graph.append_operation(operations.Aggregate(1))
    return graph

def get_prompter():
    return IntersectionPrompter()

def get_parser():
    return IntersectionParser()