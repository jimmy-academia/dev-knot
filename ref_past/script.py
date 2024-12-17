from argparse import ArgumentParser
import os
import json, jsonlines, csv
os.environ["OPENAI_API_KEY"] = 
from openai import OpenAI
client = OpenAI()
import tiktoken
from utils import calculate_token, gpt_answer, get_mem_instr
from prompt import extract_knowledge, create_script
from prompt import addition_goal_prompt, addition_example_prompt
from prompt import sorting_goal_prompt, sorting_example_prompt
from prompt import set_goal_prompt, set_example_prompt
from prompt import math_goal_prompt, math_example_prompt
from prompt import keyword_goal_prompt, keyword_example_prompt
from prompt import review_goal_prompt, review_example_prompt
from prompt import large_digit_goal_prompt, large_digit_example_prompt


# Function Define
user_struct = lambda x: {"role": "user", "content": x}
system_struct = lambda x: {"role": "system", "content": x}
assistant_struct = lambda x: {"role": "assistant", "content": x}

servant = "You follow orders strictly. Output the answer without any additional information."


parser = ArgumentParser()
parser.add_argument("dataset", default="data/all_arith/arith_08.csv")
parser.add_argument("record", default="record.txt")

args = parser.parse_args()

with open(args.dataset, 'r') as f:
    rows = csv.reader(f)
    correct = 0
    for row in rows:
        with open(args.record, 'a') as f:
            if "set_intersection" in args.dataset:
                set1 = row[1]
                set2 = row[2]
                ans = row[3]
                goal_prompt = set_goal_prompt(set1, set2)
                ex_prompt = set_example_prompt()
                f.write(set1 + '\n')
                f.write(set2 + '\n')
            else:
                seq = row[1]
                ans = row[2]
                if "arith" in args.dataset or "addmul" in args.dataset:
                    goal_prompt = math_goal_prompt(seq)
                    ex_prompt = math_example_prompt()
                elif "countries" in args.dataset:
                    goal_prompt = keyword_goal_prompt(seq)
                    ex_prompt = keyword_example_prompt()
                elif "digit" in args.dataset:
                    goal_prompt = large_digit_goal_prompt(seq)
                    ex_prompt = large_digit_example_prompt()
                elif "Review" in args.dataset:
                    goal_prompt = review_goal_prompt(seq)
                    ex_prompt = review_example_prompt()
                elif "sorting" in args.dataset:
                    goal_prompt = sorting_goal_prompt(seq)
                    ex_prompt = sorting_example_prompt()
                f.write(seq + '\n')
            
            # extract knowledge
            knowledge_prompt = extract_knowledge(goal_prompt)
            # print(knowledge_prompt)
            knowledge = gpt_answer(knowledge_prompt, "gpt-4o")
            f.write("-------------------knowledge----------------------\n")
            f.write(knowledge + '\n')
            script_prompt = create_script(goal_prompt, knowledge, ex_prompt)
            # print(script_prompt)
            script = gpt_answer(script_prompt, "gpt-4o")
            f.write("-------------------script---------------------------\n")
            f.write(script + '\n')

            # initialize memory
            memory = {}
            if "set_intersection" in args.dataset:
                memory["(Set1)"] = set1
                memory["(Set2)"] = set2
            else:
                memory["(input)"] = seq
            
            steps = script.split('\n')
            for s in steps:
                if '=' in s:
                    index = s.find('=')
                    title = s[:index]
                    instr = s[index+1:]
                    mem_instr = get_mem_instr(memory, instr)
                    f.write("--------------------mem_instr-------------------\n")
                    f.write(mem_instr + '\n')
                    res = gpt_answer(mem_instr, "gpt-4o")
                    f.write("--------------------res-------------------\n")
                    f.write(res + '\n')
                    memory[title] = res

            f.write("--------------------our_ans-------------------\n")
            f.write(str(res) + '\n')
            f.write("--------------------ans-------------------\n")
            f.write(ans + '\n')

            if str(res) == str(ans):
                f.write("correct answer !!!\n")
                correct += 1
            else:
                f.write("error !!\n")

    print(correct/100)




