import os
import sys
import time
import logging
from .base import BaseScheme

# Add schemes directory to sys.path so that 'import graph_of_thoughts' works
# This is necessary because the GoT code uses absolute imports like 'from graph_of_thoughts import ...'
schemes_dir = os.path.dirname(__file__)
if schemes_dir not in sys.path:
    sys.path.insert(0, schemes_dir)

GOT_AVAILABLE = False
try:
    import graph_of_thoughts
    from graph_of_thoughts import controller, language_models, operations
    GOT_AVAILABLE = True
    logging.info(f"Successfully loaded graph_of_thoughts")
except ImportError as e:
    logging.warning(f"graph_of_thoughts not available: {e}")
    # print(f"Error importing graph_of_thoughts: {e}")

class GraphofThought(BaseScheme):
    
    def prep_const_prompt(self):
        pass
    
    def prep_task_spcefics(self):
        self.task_name = self.args.task.split(':')[0]
        self.div = self.args.div
        
        self.task_files = {
            'keyword': 'keyword_counting/keyword.py',
            'set_intersection': 'set_intersection/intersection.py',
            'sorting': 'sorting/sorting.py',
            'arithmetic': 'arithmetic/arithmetic.py',      
            'large_digit': 'large_digit/large_digit.py',   
        }
    
    def solve_query(self, query, ground_truth=None):
        if not GOT_AVAILABLE:
            raise RuntimeError("graph_of_thoughts not available")
        
        start_time = time.time()
        
        task_file = self.task_files.get(self.task_name)
        if not task_file:
            raise ValueError(f"Task {self.task_name} not supported in GoT")
        
        try:
            task_module = self._load_task_module(task_file)
            
            # Config is now inside schemes/graph_of_thoughts/language_models/config.json
            config_path = os.path.join(
                os.path.dirname(graph_of_thoughts.__file__),
                'language_models',
                'config.json'
            )
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config not found: {config_path}")
            
            # Load and modify config to use the correct model
            import json
            import tempfile
            
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            if "chatgpt" not in config_data:
                 config_data["chatgpt"] = {"model_id": "gpt-3.5-turbo"} # default fallback
            
            config_data["chatgpt"]["model_id"] = self.args.worker_llm
            config_data["chatgpt"]["max_tokens"] = 8192 

            # Create temp config file
            temp_config = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json')
            json.dump(config_data, temp_config)
            temp_config.flush()
            temp_config.close()
            
            lm = language_models.ChatGPT(
                temp_config.name,
                model_name="chatgpt",
                cache=True
            )
 
            lm = self._patch_lm_timing(lm)
            initial_state = {
                "original": query,
                "current": "",
                "phase": 0,
                "method": "got"
            }
            
            executor = controller.Controller(
                lm,
                task_module.got(),
                task_module.get_prompter(),
                task_module.get_parser(),
                initial_state
            )
            
            executor.run()
            result = self._extract_result(executor)
            result = self._post_process(result)
            
        except Exception as e:
            logging.error(f"GoT execution failed: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        end_time = time.time()
        self.total_runtimes.append(end_time - start_time)
        
        return result
    
    def _load_task_module(self, task_file):
        import importlib.util
        
        # Examples are now in schemes/got_tasks
        examples_dir = os.path.join(os.path.dirname(__file__), 'got_tasks')
        module_path = os.path.join(examples_dir, task_file)
        
        if not os.path.exists(module_path):
            raise FileNotFoundError(f"Task module not found: {module_path}")
        
        spec = importlib.util.spec_from_file_location("task_module", module_path)
        module = importlib.util.module_from_spec(spec)
        
        if examples_dir not in sys.path:
            sys.path.insert(0, examples_dir)
        
        spec.loader.exec_module(module)
        
        return module
    
    def _patch_lm_timing(self, lm):
        if not hasattr(lm, 'generate_text'):
            return lm
        
        original_generate = lm.generate_text
        
        def timed_generate(*args, **kwargs):
            step_start = time.time()
            result = original_generate(*args, **kwargs)
            step_end = time.time()
            self.perstep_runtimes.append(step_end - step_start)
            return result
        
        lm.generate_text = timed_generate
        return lm
    
    def _extract_result(self, executor):
        try:
            final_thoughts = executor.get_final_thoughts()
            
            if not final_thoughts or len(final_thoughts) == 0:
                return None
            
            if len(final_thoughts[-1]) == 0:
                return None
            
            final_thought = final_thoughts[-1][0]
            
            if hasattr(final_thought, 'state') and 'current' in final_thought.state:
                result = final_thought.state['current']
                return result
            
            return None
        except Exception as e:
            logging.error(f"Failed to extract result: {e}")
            return None
    
    def _post_process(self, result):
        if result is None:
            logging.warning("[post_process] Result is None")
            return result
        
        task_name = self.task_name
        
        logging.info(f"[post_process] task={task_name}")
        logging.info(f"[post_process] result type={type(result)}")
        logging.info(f"[post_process] result value={result}")
        logging.info(f"[post_process] ground_truth={getattr(self, 'ground_truth', 'N/A')}")
        
        # Keyword: JSON dict -> Python list
        if task_name == 'keyword':
            if isinstance(result, str):
                try:
                    import json
                    parsed_result = json.loads(result)
                    
                    countries = []
                    if isinstance(parsed_result, dict):
                        # Handle old dict format {"Country": freq}
                        for country, freq in parsed_result.items():
                            countries.extend([country] * freq)
                    elif isinstance(parsed_result, list):
                         # Handle new list format ["Country1", "Country2"]
                        countries = parsed_result
                    else:
                        countries = []

                    logging.info(f"[post_process] Converted to list: {countries}")
                    
                    result_str = f"[{', '.join(str(c) for c in countries)}]"
                    logging.info(f"[post_process] Final output: {result_str}")
                    return result_str
                except Exception as e:
                    logging.error(f"[post_process] Failed to parse: {e}")
                    return str(result)
            return str(result)
        
        elif task_name in ['large_digit', 'arithmetic']:
            if isinstance(result, (int, float)):
                result_str = str(result)
                if task_name == 'arithmetic' and isinstance(result, float):
                    if result.is_integer():
                        result_str = str(int(result))
                    else:
                        result_str = f"{result:.2f}"
                        if result_str.endswith(".00"): result_str = result_str[:-3]
                logging.info(f"[post_process] Converted to string: {result_str}")
                return result_str
            return str(result)
        
        elif task_name in ['sorting', 'set_intersection']:
            if isinstance(result, list):
                result_str = str(result)
                logging.info(f"[post_process] Converted to string: {result_str}")
                return result_str
            return str(result)
        
        return str(result)