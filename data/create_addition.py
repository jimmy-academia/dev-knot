import random
import csv

def generate_addition_task(num_terms=50, only_add=False):
    digits = [random.randint(0, 99) for _ in range(num_terms)]
    # digits = [random.randint(0, 9) for _ in range(num_terms)]
    if only_add:
        expression = '+'.join(map(str, digits))
    else:
        expression = str(digits.pop(0))
        for d in digits:
            expression += random.choice(['+', '-', '*']) + str(d)
    
    result = sum(digits)
    
    return expression, result

def create_addition_csv(filename, num_tasks=100, num_terms=50):
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
            expression, result = generate_addition_task(num_terms)
            writer.writerow([i, expression, result])
    
    print(f"Generated {num_tasks} addition tasks in '{filename}'")

# Example usage
if __name__ == "__main__":

    for num in [5, 10, 15, 25]:
        create_addition_csv(f"data/arithmetic/nd{num}.csv", num_terms=num)
    
