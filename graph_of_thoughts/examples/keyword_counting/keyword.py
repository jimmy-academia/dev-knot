from typing import Dict, List, Union
from graph_of_thoughts import operations, prompter, parser
import json

class KeywordPrompter(prompter.Prompter):
    """Keyword counting prompter"""
    
    count_prompt = """<Instruction> Count the frequency of how many times each country is explicitly named in the input text. Output only the frequency of each country that appears at least once in the following json format:
{{
    "country1": frequency1,
    "country2": frequency2
}}
</Instruction>

<Examples>
Input:
Alexandra boarded the first flight from Canada. Her first stop was Mexico.
Output: 
{{
    "Canada": 1,
    "Mexico": 1
}}
</Examples>

Input:
{input}
Output:"""
    
    def aggregation_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        return self.count_prompt.format(input=state_dicts[0]['original'])
    
    def generate_prompt(self, num_branches: int, **kwargs) -> str:
        state = kwargs.get('state', kwargs)
        return self.count_prompt.format(input=state['original'])
    
    def improve_prompt(self, **kwargs) -> str:
        return "Improve the country counting result."
    
    def validation_prompt(self, **kwargs) -> str:
        return "Is the country counting correct? Answer 'Yes' or 'No'."
    
    def score_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        return "Rate accuracy from 0 to 1."

class KeywordParser(parser.Parser):
    
    def __init__(self):
        self.cache = {}
    
    def parse_aggregation_answer(
        self, states: List[Dict], texts: List[str]
    ) -> Union[Dict, List[Dict]]:
        new_states = []
        for text in texts:
            try:
                result = json.loads(text.strip())
                if not isinstance(result, dict):
                    result = {}
            except:
                result = {}
            
            new_state = states[0].copy()
            new_state["current"] = json.dumps(result)
            new_state["phase"] = states[0]["phase"] + 1
            new_states.append(new_state)
        
        return new_states[0] if len(new_states) == 1 else new_states
    
    def parse_generate_answer(self, state: Dict, texts: List[str]) -> List[Dict]:
        new_states = []
        for text in texts:
            try:
                result = json.loads(text.strip())
                if not isinstance(result, dict):
                    result = {}
            except:
                result = {}
            
            new_state = state.copy()
            new_state["current"] = json.dumps(result)
            new_state["phase"] = state["phase"] + 1
            new_states.append(new_state)
        
        return new_states
    
    def parse_improve_answer(self, state: Dict, texts: List[str]) -> Dict:
        text = texts[0] if texts else "{}"
        try:
            result = json.loads(text.strip())
            if not isinstance(result, dict):
                result = {}
        except:
            result = {}
        
        new_state = state.copy()
        new_state["current"] = json.dumps(result)
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
    return KeywordPrompter()

def get_parser():
    return KeywordParser()