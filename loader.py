import csv
import json
from utils import readf

from debug import *

def get_task_loader(args):
    if args.task == 'addition':
        rows = csv.reader(open(f'data/addition/{args.div}.csv'))
        loader = ((row[1], row[2]) for row in rows)
         
    if args.task == 'gsm_symbolic':
        query_list = []
        answer_list = []
        GSM_data = readf('data/GSM/GSM_symbolic.jsonl')
        for line in GSM_data:
            data = json.loads(line)
            query_list.append(data.get('question'))
            answer_list.append(data.get('answer').split('####')[1].strip())

        loader = zip(query_list, answer_list)

    return loader
