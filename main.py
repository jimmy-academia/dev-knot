import logging
import argparse

from loader import get_task_loader
from schemes import setup_scheme
from utils import set_seeds, set_verbose

def set_arguments():
    parser = argparse.ArgumentParser(description='Run experiments')
    
    # environment
    parser.add_argument('--seed', type=int, default=0, help='random seed')
    parser.add_argument('--verbose', type=int, default=1, help='verbose')
    parser.add_argument('--worker_llm', type=str, default="gpt-3.5-turbo")
    parser.add_argument('--planner_llm', type=str, default="gpt-4o")
    
    # logging decisions
    parser.add_argument('--ckpt', type=str, default='ckpt')

    # Task, prompt scheme
    parser.add_argument('--scheme', type=str, default='knot')
    parser.add_argument('--task', type=str, default='addition', choices=['addition', 'gsm_symbolic'])
    parser.add_argument('--div', type=str, default='8')

    # prevent overwrite for script/tasks when not set
    parser.add_argument('--overwrite', action='store_true')

    args = parser.parse_args()
    return args

def main():
    args = set_arguments()
    set_seeds(args.seed)
    set_verbose(args.verbose)
    
    planner_info = f'{args.planner_llm} + ' if args.scheme == 'knot' else ''
    logging.info(f'== running exp: {args.scheme} on {args.task} with {planner_info}{args.worker_llm}')

    task_loader = get_task_loader(args)
    Scheme = setup_scheme(args, task_loader) # set up scheme for task
    Scheme.prep_task_spcefics()
    Scheme.operate() # and record intermediate step/ final result


if __name__ == '__main__':
    main()