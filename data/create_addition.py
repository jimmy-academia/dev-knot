# python create_addition.py

import random
import csv

def generate_addition_task(num_terms=50, only_add=False):
    # digits = [random.randint(0, 999) for _ in range(num_terms)]
    # digits = [random.randint(0, 99) for _ in range(num_terms)]
    digits = [random.randint(0, 9) for _ in range(num_terms)]
    if only_add:
        expression = '+'.join(map(str, digits))
    else:
        expression = str(digits.pop(0))
        for d in digits:
            expression += random.choice(['+', '-', '*']) + str(d)
    
    result = sum(digits)
    
    return expression, result

def create_addition_csv(filename, num_tasks, num_terms, only_add):
    """
    Create a CSV file with pure addition tasks.
    
    Args:
        filename: Output CSV filename
        num_tasks: Number of tasks to generate
        min_terms: Minimum number of terms per expression
        max_terms: Maximum number of terms per expression
    """
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        for i in range(num_tasks):
            expression, result = generate_addition_task(num_terms, only_add)
            writer.writerow([i, expression, result])
    
    print(f"Generated {num_tasks} addition tasks in '{filename}'")

# Example usage
if __name__ == "__main__":

    only_add = True
    task = 'addition' if only_add else 'arithmetic'
    num_queries = 100
    for num in [8, 16, 32]:
        create_addition_csv(f"{task}/{num}.csv", num_queries, num, only_add)
    
