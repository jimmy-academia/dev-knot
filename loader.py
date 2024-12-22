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
        gsm_div = {'0': "symbolic", "1":"p1", "2":"p2"}

        GSM_data = readf(f'data/GSM/GSM_{gsm_div[args.div]}.jsonl')
        count = 0
        for line in GSM_data.split('\n'):
            data = json.loads(line)
            query_list.append(data.get('question'))
            answer_list.append(data.get('answer').split('####')[1].strip())
            count += 1
            if count == 104:
                break
        loader = zip(query_list, answer_list)

    return loader
