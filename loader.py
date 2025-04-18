import csv
import json
from utils import readf

from debug import *

def get_task_loader(args):

    if args.task in ['yelp', '']:
        file = f'data/{args.task}/{args.div}.csv' if args.div else f'data/{args.task}.csv'
        rows = csv.reader(open(file))
        if args.task == 'intersection':
            loader = ((row[1], row[2], row[3]) for row in rows) 
        else:
            loader = ((row[1], row[2]) for row in rows) 

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

    if args.task == 'game24':
        rows = csv.reader(open(f'data/game24/24.csv'))
        next(rows)
        loader = ((row[1], None) for row in rows)

    return loader
