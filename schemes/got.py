import os
import sys
import time
import logging
from .base import BaseScheme

GOT_ROOT = os.path.join(os.path.dirname(__file__), '..', 'graph_of_thoughts')
if os.path.exists(GOT_ROOT):
    sys.path.insert(0, GOT_ROOT)
    GOT_PKG = os.path.join(GOT_ROOT, 'graph_of_thoughts')
    if GOT_PKG not in sys.path:
        sys.path.insert(0, GOT_PKG)

GOT_AVAILABLE = False
try:
    from graph_of_thoughts import controller, language_models, operations
    GOT_AVAILABLE = True
    logging.info(f"Successfully loaded graph_of_thoughts")
except ImportError as e:
    logging.warning(f"graph_of_thoughts not available: {e}")

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
    
    def solve_query(self, query):
        if not GOT_AVAILABLE:
            raise RuntimeError("graph_of_thoughts not available")
        
        start_time = time.time()
        
        task_file = self.task_files.get(self.task_name)
        if not task_file:
            raise ValueError(f"Task {self.task_name} not supported in GoT")
        
        try:
            task_module = self._load_task_module(task_file)
            
            config_path = os.path.join(
                GOT_ROOT,
                'graph_of_thoughts',
                'language_models',
                'config.json'
            )
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config not found: {config_path}")
            
            lm = language_models.ChatGPT(
                config_path,
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
        
        examples_dir = os.path.join(GOT_ROOT, 'examples')
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
                    country_dict = json.loads(result)
                    # 将 {"Country": freq} 转换为 [Country, Country, ...]
                    countries = []
                    for country, freq in country_dict.items():
                        countries.extend([country] * freq)
                    logging.info(f"[post_process] Converted to list: {countries}")
                    
                    result_str = str(countries)
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
                    result_str = f"{result:.2f}"
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