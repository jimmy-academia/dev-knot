import openai
import logging
from collections import defaultdict
from utils import readf, user_struct, system_struct, dumpj

Few_Shot_Example = {
    'yelp': ,
    'keyword': ,
    'sorting': {
        '8':
        '16':
        '32':
    },
    'intersection': {
        '32':
        '64':
        '128':
    },
    'arithmetic': {
        '8':
        '16':
        '32':
    },
    'large_digit': {
        '8':
        '16':
        '32':
    },
}

class BaseScheme(object):
    def __init__(self, args, task_loader):
        super(BaseScheme, self).__init__()
        self.args = args
        self.task_loader = task_loader
        self.check_openai_api()

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

    def llm_call(self, message, model=self.args.worker_llm, temperature=0):
        response = self.client.chat.completions.create(
                    model = model,
                    messages = message,
                    temperature = temperature,
                )
        response = response.choices[0].message.content
        return response

    def prep_const_prompt(self):
        self.system_servent = "You follow orders strictly. Output the answer without any additional information."

    def prep_task_spcefics(self):
        if args.scheme == 'few' 
            self.examples = Few_Shot_Example.get(self.args.task).get(self.args.div)
        else: 
            self.examples = ""

    def solve_query(self, query):
        return self.llm_call([system_struct(self.system_servent), user_struct(query + " " + self.examples)])
    
    def operate(self):

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

