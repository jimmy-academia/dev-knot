import openai
import logging
from collections import defaultdict
from utils import readf, user_struct, system_struct, dumpj

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

    def llm_call(self, message, model=None, temperature=0):
        if model is None:
            model = self.args.worker_llm
        response = self.client.chat.completions.create(
                    model = model,
                    messages = message,
                    temperature = temperature,
                )
        response = response.choices[0].message.content
        return response

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


class ZeroFewShot(BaseScheme):
    def prep_const_prompt(self):
        self.system_servent = "You follow orders strictly. Output the answer without any additional information."
    def prep_task_spcefics(self):
        if args.scheme == 'few':
            self.examples = Few_Shot_Example.get(self.args.task).get(self.args.div)
        else: 
            self.examples = ""
    def solve_query(self, query):
        return self.llm_call([system_struct(self.system_servent), user_struct(query + " " + self.examples)])


Few_Shot_Example = {
    'yelp': """
Input: ["The food was incredible and the service was top-notch! Would definitely recommend this place to anyone.", 
        "Terrible experience, waited for an hour and the food was cold.", 
        "Had a great time, the atmosphere was wonderful and staff very attentive.",
        "Overpriced and disappointing, won't be coming back."]
Answer: 2
""",
    
    'keyword': """
Input: "John, an avid traveler from Canada, had spent his summer exploring the heart of Australia. The vast, arid landscapes of Australia presented a stark contrast to the snow-filled winters of his home in Canada, and he reveled in the difference. After Australia, he visited Japan for a week."
Answer: 5
""",
    
    'sorting': {
        '8': """
Input: [6, 3, 7, 1, 5, 0, 2, 4]
Answer: [0, 1, 2, 3, 4, 5, 6, 7]
""",
        '16': """
Input: [9, 3, 5, 7, 1, 8, 6, 0, 2, 4, 5, 3, 1, 7, 8, 4]
Answer: [0, 1, 1, 2, 3, 3, 4, 4, 5, 5, 6, 7, 7, 8, 8, 9]
""",
        '32': """
Input: [3, 0, 8, 5, 7, 1, 2, 9, 4, 6, 3, 8, 0, 7, 5, 1, 9, 2, 4, 6, 3, 0, 8, 5, 7, 1, 2, 9, 4, 6, 3, 8]
Answer: [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 8, 9, 9, 9]
"""
    },
    
    'intersection': {
        '32': """
Input: 
Set1: [11, 60, 1, 49, 21, 33, 14, 56, 54, 15, 23, 40, 45, 22, 7, 28, 20, 46, 51, 6, 34, 37, 3, 50, 17, 8, 25, 0, 35, 47, 18, 19]
Set2: [31, 11, 4, 63, 38, 58, 59, 24, 61, 14, 32, 39, 27, 46, 48, 19, 52, 57, 50, 56, 3, 2, 53, 29, 5, 37, 62, 41, 36, 12, 49, 16]
Answer: [11, 14, 19, 46, 49, 50, 56, 3, 37]
""",
        '64': """
Input:
Set1: [42, 73, 86, 39, 85, 77, 69, 59, 43, 127, 121, 88, 109, 53, 70, 66, 25, 51, 34, 78, 45, 11, 40, 99, 68, 47, 49, 41, 101, 31, 24, 84, 36, 29, 118, 75, 3, 27, 30, 80, 125, 8, 37, 46, 90, 21, 60, 83, 19, 6, 95, 117, 87, 18, 100, 13, 22, 10, 110, 102, 35, 81, 17, 63]
Set2: [34, 49, 116, 106, 112, 23, 5, 80, 18, 62, 90, 54, 32, 103, 37, 43, 9, 25, 92, 16, 111, 79, 64, 91, 107, 58, 72, 94, 7, 60, 33, 14, 19, 104, 28, 74, 96, 76, 38, 52, 114, 50, 17, 0, 3, 100, 69, 98, 2, 1, 99, 12, 95, 97, 123, 4, 126, 124, 82, 27, 67, 57, 115, 46]
Answer: [34, 49, 80, 18, 90, 37, 25, 60, 19, 17, 3, 100, 69, 95, 27, 46]
""",
        '128': """
Input:
Set1: [132, 75, 157, 25, 199, 202, 147, 109, 221, 110, 220, 251, 213, 11, 224, 101, 200, 170, 155, 71, 119, 122, 39, 1, 29, 113, 189, 212, 10, 219, 49, 28, 151, 40, 103, 8, 145, 214, 114, 91, 175, 107, 152, 163, 148, 246, 176, 181, 18, 106, 74, 115, 144, 0, 205, 121, 46, 234, 142, 223, 228, 162, 96, 97, 130, 156, 172, 241, 33, 186, 137, 150, 65, 161, 226, 116, 111, 12, 146, 38, 167, 4, 108, 169, 61, 93, 190, 252, 22, 31, 3, 9, 13, 35, 23, 141, 129, 198, 85, 84, 62, 158, 201, 67, 117, 59, 41, 191, 56, 90, 51, 227, 143, 83, 184, 174, 125, 98, 232, 238, 57, 225, 54, 179, 177, 237, 37, 95]
Set2: [27, 162, 187, 254, 128, 227, 2, 165, 143, 109, 140, 46, 160, 26, 139, 171, 42, 199, 207, 30, 205, 117, 213, 48, 40, 212, 185, 196, 197, 94, 136, 35, 229, 193, 36, 7, 15, 43, 4, 203, 142, 144, 49, 31, 240, 124, 116, 69, 37, 250, 95, 105, 103, 168, 126, 64, 73, 206, 24, 157, 135, 118, 34, 134, 45, 62, 153, 5, 47, 239, 216, 222, 80, 231, 102, 21, 57, 215, 149, 141, 236, 32, 188, 204, 194, 23, 233, 83, 154, 210, 159, 70, 202, 253, 20, 71, 166, 242, 221, 228, 78, 230, 29, 145, 147, 81, 104, 235, 66, 100, 131, 132, 244, 195, 68, 72, 53, 182, 79, 248, 3, 82, 211, 173, 180, 17, 77, 51]
Answer: [157, 25, 199, 109, 221, 227, 117, 213, 40, 143, 46, 142, 49, 31, 116, 37, 95, 103, 162, 35, 4, 144, 62, 23, 83, 3, 57, 90, 51, 202, 228, 29]
"""
    },
    
    'arithmetic': {
        '8': """
Input: 6+4+3+3*3+2+4+2
Answer: 30
""",
        '16': """
Input: 2/9-3-4+6+4-9+8+8-4*5-7+2/1+6+7
Answer: -1.78
""",
        '32': """
Input: 8-2/2/9+9*1/7/3*4+2/5-9+4*8+5+8+9+5+5-2+7/2-2+6-8+7+6+5+1+6*3+1
Answer: 75.94
"""
    },
    
    'large_digit': {
        '8': """
Input: 57247728+67594862
Answer: 124842590
""",
        '16': """
Input: 5465458164972518+8654164596886757
Answer: 14119622761859275
""",
        '32': """
Input: 59842829133617473427166884252972+24873376371863371698982744892145
Answer: 84716205505480845126149629145117
"""
    },
    
    'addition': {
        '8': """
Input: 6+4+3+3+2+4+2
Answer: 24
""",
        '16': """
Input: 2+9+3+4+6+4+9+8+8+4+5+7+2+6+7
Answer: 84
""",
        '32': """
Input: 8+2+9+9+7+3+4+2+5+9+4+8+5+8+9+5+5+2+7+2+2+6+8+7+6+5+1+6+3+1+1+2
Answer: 160
"""
    },
}


'''
import logging
from .base import BaseScheme

class PromptScheme(BaseScheme):
    def prep_const_prompt(self):
        pass
    def prep_task_spcefics(self):
        pass

    def solve_query(self, query):
        pass

'''