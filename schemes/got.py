import os
import logging
import importlib
from pathlib import Path

from .base import BaseScheme
from .graph_of_thoughts import controller
from .graph_of_thoughts.language_models import ChatGPT

class GraphofThought(BaseScheme):
    """
    Graph of Thoughts (GoT) implementation for the dev-knot framework.
    This adapts the existing GoT examples to work within the BaseScheme structure.
    """
    def prep_const_prompt(self):
        pass

    def prep_task_spcefics(self):
        module_name = f'.graph_of_thoughts.examples.{self.args.task}.{self.args.div}'
        try:
            module = importlib.import_module(module_name, package='schemes')
            self.prompter = module.Prompter()
            self.parser = module.Parser()
            self.operations_graph = module.got()
        except:
            raise ImportError(f"Module '{module_name}' is not implemented.")

    def solve_query(self, query):
        """
        Solve the query using the Graph of Thoughts approach.
        """
        # Get config path
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "graph_of_thoughts/language_models/config.json",
        )
        
        # Initialize language model
        lm = ChatGPT(
            config_path,
            model_name=self.args.worker_llm,
            cache=True,
        )
        
        # Set up initial state
        init_state = {
            "original": query,
            "current": "",
            "phase": 0,
            "method": "got",
        }
        
        # Create and run controller
        executor = controller.Controller(
            lm,
            self.operations_graph,
            self.prompter,
            self.parser,
            init_state,
        )
        
        try:
            executor.run()
            
            # Get final thoughts
            final_thoughts = executor.get_final_thoughts()
            if final_thoughts and final_thoughts[0]:
                output = final_thoughts[0][0].state.get("current", "")
                logging.info(f">>>>>>> final result: {output} <<<<<<")
                return output
            else:
                logging.error("No final thoughts generated")
                return "Failed to solve"
            
        except Exception as e:
            logging.error(f"Exception in GoT solver: {e}")
            return f"Error: {str(e)}"