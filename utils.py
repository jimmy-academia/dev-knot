import re
import os
import json
import argparse
import random
import logging
import statistics


user_struct = lambda x: {"role": "user", "content": x}
system_struct = lambda x: {"role": "system", "content": x}
assistant_struct = lambda x: {"role": "assistant", "content": x}


def set_seeds(seed):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def set_verbose(verbose):
    # usages: logging.warning; logging.error, logging.info, logging.debug
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    if verbose == 0:
        level = logging.WARNING
    elif verbose == 1:
        level = logging.INFO
    elif verbose == 2:
        level = logging.DEBUG
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        handlers=[logging.StreamHandler()],  # Print to terminal
    )


class NamespaceEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, argparse.Namespace):
      return obj.__dict__
    else:
      return super().default(obj)

def dumpj(dictionary, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        obj = json.dumps(dictionary, indent=4, cls=NamespaceEncoder, ensure_ascii=False)
        obj = re.sub(r'("|\d+),\s+', r'\1, ', obj)
        obj = re.sub(r'\[\n\s*("|\d+)', r'[\1', obj)
        obj = re.sub(r'("|\d+)\n\s*\]', r'\1]', obj)
        f.write(obj)

def loadj(filepath):
    with open(filepath) as f:
        return json.load(f)

def readf(path):
    with open(path, 'r') as f:
        return f.read()

def worst_meanstd(_list):
    if not _list:
        return 0.0, 0.0, 0.0
    if len(_list) == 1:
        return _list[0], _list[0], 0.0
    return max(_list), statistics.mean(_list), statistics.stdev(_list)


def extract_json_content(text):
    """
    Robustly extract the first valid JSON list or object from a string.
    Handles nested structures by counting brackets.
    """
    text = text.strip()
    
    # helper to find the balancing bracket
    def find_end(s, start_idx, open_char, close_char):
        count = 0
        for i in range(start_idx, len(s)):
            if s[i] == open_char:
                count += 1
            elif s[i] == close_char:
                count -= 1
                if count == 0:
                    return i + 1
        return -1

    candidates = []
    
    # Find all potential starts
    for i, char in enumerate(text):
        if char == '[':
            end = find_end(text, i, '[', ']')
            if end != -1:
                candidates.append(text[i:end])
        elif char == '{':
            end = find_end(text, i, '{', '}')
            if end != -1:
                candidates.append(text[i:end])
                
    # Return the first candidate that parses as JSON
    import json
    import ast
    
    for cand in candidates:
        try:
            return json.loads(cand)
        except:
            try:
                return ast.literal_eval(cand)
            except:
                continue
                
    # Fallback: Regex for simple list
    import re
    match = re.search(r'\[.*?\]', text, re.DOTALL)
    if match:
        try: return json.loads(match.group(0))
        except: 
            try: return ast.literal_eval(match.group(0))
            except: pass
            
    return text  # Return original if everything fails
