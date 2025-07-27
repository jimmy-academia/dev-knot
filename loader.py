import csv
import json
from utils import readf, loadj

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
        file = f'data/{args.task}/{args.div}.csv'
        rows = csv.reader(open(file))
        return [(row[1], row[2]) for row in rows]

    # Handle intersection which needs 3 columns
    if args.task == 'intersection':
        file = f'data/{args.task}/{args.div}.csv' if args.div else f'data/{args.task}.csv'
        rows = csv.reader(open(file))
        return [(row[1], row[2], row[3]) for row in rows]
         
    if args.task == 'healthcare':
        workflows = loadj("data/healthcare/workflows.json")
        workflow_dict = {w["workflow_name"]: w["logic_flow"] for w in workflows}
        
        query_list = []
        answer_list = []
        with open("data/healthcare/triage_benchmark_dataset.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                query = row["query"]
                workflow_name = row["workflow"]
                answer = row["answer"]

                # (Optional) Get the logic flow if needed
                logic_flow = workflow_dict.get(workflow_name, "")

                # print(query)
                # print()
                # print(logic_flow)
                # print()
                # print(answer)
                # input()
                # Append to lists
                query_list.append(query + '\n rule-based triage workflow:\n' + logic_flow)
                answer_list.append(answer)

        return zip(query_list, answer_list)

    # Handle GSM symbolic task
    if args.task == 'gsm_symbolic':
        query_list = []
        answer_list = []
        gsm_div = {'0': "symbolic", "1":"p1", "2":"p2"}

        GSM_data = readf(f'data/_gsm_symbolic/GSM_{gsm_div[args.div]}.jsonl')
        count = 0
        for line in GSM_data.split('\n'):
            data = json.loads(line)
            query_list.append(data.get('question'))
            answer_list.append(data.get('answer').split('####')[1].strip())
            count += 1
            if count == 100:
                break
        return zip(query_list, answer_list)

    if args.task == 'gsm8k':
        from datasets import load_from_disk
        dataset = load_from_disk("data/gsm8k/")
        query_list = []
        answer_list = []
        problem_id = 0
        for i in range(100):
            query = ''
            answer = 0
            for k in range(int(args.div)):
                if problem_id in [2]:
                    problem_id += 1
                query += f"Problem {k}: {dataset['test'][problem_id]['question']}\n"
                answer += int(dataset['test'][problem_id]['answer'].split('#### ')[1].replace(",", ""))

                problem_id += 1

            query += "Final Problem: what is the sum of the answers from all of the problems?"
            query_list.append(query)
            answer_list.append(answer)

        return zip(query_list, answer_list)
         
    # Handle game24 task
    if args.task == 'game24':
        rows = csv.reader(open(f'data/game24/24.csv'))
        next(rows)  # Skip header
        return [(row[1], None) for row in rows]

def test():
    tasks_to_test = ['healthcare']
    # tasks_to_test = ['keyword', 'arithmetic', 'sorting', 'large_digit', 'intersection']
    
    # Define the divisions to test for each task
    divs = {'yelp': '', 'keyword': '1', 'addition': '8', 'arithmetic': '8', 
            'sorting': '16', 'large_digit': '8', 'intersection': '32', 'healthcare': ''}
    
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

if __name__ == "__main__":
    test()
