### dev xnot
# python main.py

import logging
import argparse
from pathlib import Path

from loader import get_task_loader
from schemes import setup_scheme
from utils import set_seeds, set_verbose

from debug import check
import os

def set_arguments():
    parser = argparse.ArgumentParser(description='Run experiments')
    
    # environment
    # gpt-3.5-turbo, gpt-4o
    parser.add_argument('--seed', type=int, default=0, help='random seed')
    parser.add_argument('--verbose', type=int, default=1, help='verbose')
    parser.add_argument('--planner_llm', type=str, default="gpt-5-nano") 
    parser.add_argument('--worker_llm', type=str, default="gpt-5-nano")

    # logging decisions
    parser.add_argument('--ckpt', type=str, default='ckpt')
    parser.add_argument('--threads', type=int, default=1, help='number of threads for parallel processing')

    # Task, prompt scheme
    parser.add_argument('--scheme', type=str, default='xnot') 
    parser.add_argument('--task', type=str, default='healthcare')
    # yelp:[10, 20, 30], keyword:[4, 2, 1], sorting:[16, 32, 64], intersection:[32, 64, 128], arithmetic:[8, 16, 32], large_digit:[8, 16, 32]
    # addition:[8, 16, 32]; game24; gsm8k

    args = parser.parse_args()
    args.task, args.div = (args.task.split(':') + [None])[:2]
    return args

def main():
    args = set_arguments()

    # if args.task == 'healthcare':
    #     args.planner_llm = "gpt-4.1"
    #     # args.worker_llm = "chatgpt-4o-latest"
    #     # args.worker_llm = "gpt-4o-mini"
    # if args.scheme == 'rknot':
    #     args.planner_llm = "o1-mini"
    #     args.worker_llm = "chatgpt-4o-latest"

    args.overwrite=True
    set_seeds(args.seed)
    set_verbose(args.verbose)

    Path('output').mkdir(exist_ok=True)
    args.record_path = Path(f'output/{args.scheme}_{args.task}_{args.div}_{args.worker_llm}.json')
    if args.record_path.exists() and not args.overwrite:
        logging.info(f'{args.record_path} exists')
        return

    planner_info = f'{args.planner_llm} +> ' if 'xnot' in args.scheme else ''
    logging.info(f'== running exp: {args.scheme} on {args.task}:{args.div} with {planner_info}{args.worker_llm}')

    task_loader = get_task_loader(args)
    
    output_dir = os.path.join("output", args.task, args.scheme)
    os.makedirs(output_dir, exist_ok=True)

    args.record_path = os.path.join(
        output_dir,
        f"{args.task}_{args.scheme}_{args.div}_{args.worker_llm}.json"
    )
    
    Scheme = setup_scheme(args, task_loader) # set up scheme for task
    Scheme.operate() # and record intermediate step/ final result


if __name__ == '__main__':
    main()