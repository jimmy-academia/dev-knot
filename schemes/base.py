import openai
import logging
from collections import defaultdict
from utils import readf, user_struct, system_struct, dumpj

class BaseScheme(object):
    def __init__(self, args, task_loader):
        super(BaseScheme, self).__init__()
        self.args = args
        self.task_loader = task_loader
        if 'gpt' in self.args.planner_llm or 'gpt' in self.args.worker_llm:
            self.check_openai_api()

        self.prep_const_prompt()
        self.system_servent = "You follow orders strictly. Output the answer without any additional information."

    def check_openai_api(self):
        self.client = openai.OpenAI(api_key=readf('.openaiapi_key'))

        # Configure the httpx logger - this is what OpenAI uses internally
        httpx_logger = logging.getLogger("httpx")
        httpx_logger.setLevel(logging.WARNING)  # Suppress INFO logs completely
        
        # Or if you want to see httpx logs as DEBUG instead of INFO:
        class InfoToDebugFilter(logging.Filter):
            def filter(self, record):
                if record.levelno == logging.INFO:
                    record.levelno = logging.DEBUG
                    record.levelname = 'DEBUG'
                return True
        
        httpx_logger.addFilter(InfoToDebugFilter())
    
    def operate(self):

        if self.args.task == 'game24':
            idx = 0
            results = []
            for query, answer in self.task_loader:
                idx += 1
                if idx > 201:
                    break
                output = self.solve_query(query)
                results.append({
                    'idx': idx,
                    'query': query,
                    'output': output,
                    })
                dumpj(results, self.args.record_path)
            dumpj(results, self.args.record_path)

        else:
            results = defaultdict(list)
            results['accuracy'] = 0
            correct = total = 0

            for query, answer in self.task_loader:
                output = self.solve_query(query)
                logging.info(f'=> output: {output} vs answer {answer} <<<')

                results['query'].append(query)
                results['output'].append(output)
                results['answer'].append(answer)
                correct += int(output == answer)
                total += 1
                results['accuracy'] = correct/total

            results['info'] = f"Correct: {correct}/Total: {total}"
            dumpj(results, self.args.record_path)

    def llm_answer(self, prompt, planner=False, temperature=0):
        model = self.args.planner_llm if planner else self.args.worker_llm
        if 'gpt' in model:
            message = [system_struct(self.system_servent), user_struct(prompt)]
            # logging.info(" <<<< input prompt")
            # logging.info(message)
            response = self.client.chat.completions.create(
                        model = model,
                        messages = message,
                        temperature = temperature,
                    )
            response = response.choices[0].message.content
            # logging.info(" >>>> \n" + response)
        else:
            print('llama!')

        return response
