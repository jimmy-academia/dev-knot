import csv
import json
from utils import readf

from debug import *

def get_task_loader(args):
    """
    Returns a loader function for the specified task.
    
    Args:
        args: Command line arguments containing task and div information.
        
    Returns:
        A generator that yields (query, answer) tuples for the task.
    """

    # Handle tasks that use basic CSV loading pattern
    standard_csv_tasks = ['yelp', 'keyword', 'addition', 'arithmetic', 'sorting', 'large_digit']
    if args.task in standard_csv_tasks:
        file = f'data/{args.task}/{args.div}.csv' if args.div else f'data/{args.task}.csv'
        rows = csv.reader(open(file))
        return ((row[1], row[2]) for row in rows) 

    # Handle intersection which needs 3 columns
    if args.task == 'intersection':
        file = f'data/{args.task}/{args.div}.csv' if args.div else f'data/{args.task}.csv'
        rows = csv.reader(open(file))
        return ((row[1], row[2], row[3]) for row in rows)
         
    # Handle GSM symbolic task
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
            if count == 100:
                break
        return zip(query_list, answer_list)

    # Handle game24 task
    if args.task == 'game24':
        rows = csv.reader(open(f'data/game24/24.csv'))
        next(rows)  # Skip header
        return ((row[1], None) for row in rows)


if __name__ == "__main__":
    # Define the tasks to test (excluding game24 and gsm_symbolic)
    tasks_to_test = ['yelp', 'keyword', 'arithmetic', 'sorting', 'large_digit', 'intersection']
    
    # Define the divisions to test for each task
    divs = {'yelp': '', 'keyword': '', 'addition': '8', 'arithmetic': '8', 
            'sorting': '16', 'large_digit': '8', 'intersection': '32'}
    
    # Create a simple args object
    class Args:
        def __init__(self, task, div):
            self.task = task
            self.div = div
    
    # Test each task
    for task in tasks_to_test:
        print(f"\n{'='*20} TASK: {task} {'='*20}")
        
        # Create args for this task
        args = Args(task, divs[task])
        
        # Get the loader for this task
        loader = get_task_loader(args)
        
        # Print the first 3 examples
        for i, example in enumerate(loader):
            if i >= 3:
                break
                
            print(f"Example {i+1}:")
            if task == 'intersection':
                query1, query2, answer = example
                print(f"  Set1: {query1}")
                print(f"  Set2: {query2}")
                print(f"  Answer: {answer}")
            else:
                query, answer = example
                print(f"  Query: {query}")
                print(f"  Answer: {answer}")
            print()