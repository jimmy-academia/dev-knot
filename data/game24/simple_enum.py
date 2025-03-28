import itertools

def generate_array_expressions(items):
    """
    Generate arithmetic expressions using array index notations
    with only +, -, and * operations.
    
    Args:
        items: A list of array index strings
        
    Returns:
        A list of expression strings
    """
    # Use only addition, subtraction and multiplication
    operations = ['+', '-', '*']
    
    # Generate all possible permutations of array items
    item_permutations = list(itertools.permutations(items))
    
    expressions = []
    num_permutations = len(item_permutations)
    num_operation_combinations = len(operations) ** (len(items) - 1)
    expected_count = num_permutations * num_operation_combinations
    print(f"Expected expressions: {num_permutations} permutations × {num_operation_combinations} operation combinations = {expected_count}")
    
    # For each permutation of array items
    for perm in item_permutations:
        # For each possible arrangement of operations between items
        # We need (n-1) operations for n items
        for ops in itertools.product(operations, repeat=len(perm)-1):
            # Build the expression
            expression = perm[0]
            for i in range(len(ops)):
                expression += f"{ops[i]}{perm[i+1]}"
            
            expressions.append(expression)
    
    # Remove duplicates if any
    unique_expressions = list(set(expressions))
    
    return unique_expressions

def writef(path, content):
    """
    Write content to a file.
    
    Args:
        path: Output file path
        content: String content to write
    """
    with open(path, 'w') as f:
        f.write(content)

def main():
    # Array index items
    items = ['{(0)}[0]', '{(0)}[1]', '{(0)}[2]', '{(0)}[3]']
    output_file = "schemes/simple_enum4"

    print(f"Generating expressions using array indices: {items}")
    
    # Generate all expressions and store in a list
    all_expressions = generate_array_expressions(items)
    
    # Convert the list to a string with one expression per line
    content = "["+",".join(all_expressions)+"]"
    
    # Write the content to a file using the provided function
    writef(output_file, content)
    
    print(f"\nGenerated {len(all_expressions)} unique expressions")
    print(f"Results written to {output_file}")
    
    # Print a sample of the first 10 expressions
    if all_expressions:
        print("\nSample of expressions:")
        for i, expr in enumerate(all_expressions[:10], 1):
            print(f"{i}. {expr}")
        if len(all_expressions) > 10:
            print("...")
    
    # You can now use all_expressions list for further processing
    print("\nThe 'all_expressions' list contains all generated expressions.")
    print(f"Length of list: {len(all_expressions)}")

if __name__ == "__main__":
    main()