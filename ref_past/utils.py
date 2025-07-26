import os
import time
import tiktoken

def readf(path):
    with open(path, 'r') as f:
        return f.read()
        
os.environ["OPENAI_API_KEY"] = readf('../.openaiapi_key')
from openai import OpenAI
client = OpenAI()

# Function Define
user_struct = lambda x: {"role": "user", "content": x}
system_struct = lambda x: {"role": "system", "content": x}
assistant_struct = lambda x: {"role": "assistant", "content": x}

servant = "You follow orders strictly. Output the answer without any additional information."

def calculate_token(prompt):
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(prompt))
    return num_tokens

def gpt_answer(prompt, model="gpt-3.5-turbo"):
    message = [
        system_struct(servant),
        user_struct(prompt)
    ]
    response = ""
    while response == "":
        try:
            response = client.chat.completions.create(
                model = model,
                messages = message,
                temperature = 0,
            )
        except:
            time.sleep(3)
    # time.sleep(1)

    # calculate token
    all_tok = calculate_token(prompt)
    # if model == "gpt-3.5-turbo":
    #     print((all_tok/1000000)*0.5)
    # else:
    #     print((all_tok/1000000)*5)
    # print(all_tok)
    all_tok = calculate_token(str(response))
    # if model == "gpt-3.5-turbo":
    #     print((all_tok/1000000)*1.5)
    # else:
    #     print((all_tok/1000000)*15)
    # print(all_tok)


    return response.choices[0].message.content

def get_mem_instr(memory, instr):
    try:
        while '{' in instr:
            first = instr.rfind('{')
            second = instr.rfind('}')
            res = memory[instr[first+1:second]]
            res = res.replace('{', '[').replace('}', ']')
            if second+1 < len(instr) and instr[second+1] == '[':
                for i in range(second+1, len(instr)):
                    if instr[i] == ']':
                        tail = i
                        break
                res = eval(res)
                if type(res) == int:
                    res = str(res)
                    res = res[eval(f'{instr[second+2:tail]}')]
                else:
                    res = eval(f'{res}{instr[second+1:tail+1]}')
                if tail+1 < len(instr) and instr[tail+1] == '[':
                    for i in range(tail+1, len(instr)):
                        if instr[i] == ']':
                            tail_2 = i
                            break
                    if type(res) == str:
                        res = res[eval(f'{instr[tail+2:tail_2]}')]
                    else:
                        res = eval(f'{res}{instr[tail+1:tail_2+1]}')
                else:
                    tail_2 = tail
                # if type(res) == list:
                #     if ':' in num:
                #         s = num.split(':')
                #         if s[0] != '':
                #             res = res[int(s[0]):]
                #         else:
                #             res = res[:int(s[1])]
                #     else:
                #         if int(num) > len(res)-1:
                #             break
                #         else:
                #             res = res[int(num)]
                    
                instr = instr.replace(instr[first:tail_2+1], str(res))
            else:
                instr = instr.replace(instr[first:second+1], str(res))
    except:
        instr = "Output an empty array."
    return instr



