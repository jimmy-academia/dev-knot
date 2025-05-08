### dev knot

import logging
import argparse
from pathlib import Path

from loader import get_task_loader
from schemes import setup_scheme
from utils import set_seeds, set_verbose

from debug import check

def set_arguments():
    parser = argparse.ArgumentParser(description='Run experiments')
    
    # environment
    # gpt-3.5-turbo, gpt-4o
    parser.add_argument('--seed', type=int, default=0, help='random seed')
    parser.add_argument('--verbose', type=int, default=1, help='verbose')
    parser.add_argument('--planner_llm', type=str, default="gpt-4o-2024-08-06") 
    parser.add_argument('--worker_llm', type=str, default="gpt-3.5-turbo-0125")

    # logging decisions
    parser.add_argument('--ckpt', type=str, default='ckpt')

    # Task, prompt scheme
    parser.add_argument('--scheme', type=str, default='5rknot') #knot, cot
    parser.add_argument('--task', type=str, default='game24')
    # yelp, keyword, sorting:[16, 32, 64], intersection:[32, 64, 128], arithmetic:[8, 16, 32], large_digit:[8, 16, 32]
    # addition:[8, 16, 32]; gsm_symbolic:[0,1,2]...

    args = parser.parse_args()
    args.task, args.div = (args.task.split(':') + [None])[:2]
    return args

def main():
    args = set_arguments()

    if args.scheme == '5rknot':
        # args.planner_llm = "chatgpt-4o-latest"
        # args.planner_llm = "o1-mini"
        args.worker_llm = "chatgpt-4o-latest"

    args.overwrite=True
    set_seeds(args.seed)
    set_verbose(args.verbose)

    Path('output').mkdir(exist_ok=True)
    args.record_path = Path(f'output/{args.scheme}_{args.task}_{args.worker_llm}.json')
    if args.record_path.exists() and not args.overwrite:
        logging.info(f'{args.record_path} exists')
        return

    planner_info = f'{args.planner_llm} +> ' if 'knot' in args.scheme else ''
    logging.info(f'== running exp: {args.scheme} on {args.task} with {planner_info}{args.worker_llm}')

    task_loader = get_task_loader(args)
    Scheme = setup_scheme(args, task_loader) # set up scheme for task
    Scheme.prep_task_spcefics()
    Scheme.operate() # and record intermediate step/ final result


if __name__ == '__main__':
    main()