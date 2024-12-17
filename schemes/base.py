import openai
import logging
from utils import readf, user_struct, system_struct

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
        self.client = openai.OpenAI(api_key=readf('keys/openaiapi'))
    
    def operate(self):
        input('STOP!!! do code for save results first before wasting token!!!')
        input('STOP!!! do code for save results first before wasting token!!!')
        input('STOP!!! do code for save results first before wasting token!!!')
        input('STOP!!! do code for save results first before wasting token!!!')
        input('STOP!!! do code for save results first before wasting token!!!')

        results = []
        for query, answer in self.task_loader:
            output = self.solve_query(query)
            results.append([output, answer, int(output == query)])

    def llm_answer(self, prompt, planner=False):
        model = self.args.planner_llm if planner else self.args.worker_llm
        if 'gpt' in model:
            message = [system_struct(self.system_servent), user_struct(prompt)]
            logging.info(message)
            response = self.client.chat.completions.create(
                        model = model,
                        messages = message,
                        temperature = 0,
                    )
            response = response.choices[0].message.content
            logging.info(">>>" + response)
        else:
            print('llama!')

        return response
