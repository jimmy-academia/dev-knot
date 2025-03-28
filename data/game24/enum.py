import itertools
import os

def generate_all_expressions(items):
    """
    Generate all possible arithmetic expressions using the given list of items.
    
    Args:
        items: List of input items (strings)
        
    Returns:
        A list of expression strings
    """
    if len(items) == 1:
        # Base case: just the item itself
        return [items[0]]
    
    operations = ['+', '-', '*', '/']
    expressions = []
    
    # For each possible way to split the list
    for i in range(1, len(items)):
        # Get all expressions for the left part
        left_exprs = generate_all_expressions(items[:i])
        # Get all expressions for the right part
        right_exprs = generate_all_expressions(items[i:])
        
        # Combine all left expressions with all right expressions
        for left in left_exprs:
            for right in right_exprs:
                for op in operations:
                    # Add parenthesized expression
                    expressions.append(f"({left}) {op} ({right})")
    
    return expressions

def generate_expressions_with_permutations(items):
    """
    Generate all possible expressions by considering all permutations of the input items.
    
    Args:
        items: List of input items (strings)
        
    Returns:
        List of expression strings
    """
    import itertools
    
    all_expressions = []
    # Generate all permutations of the input items
    for perm in itertools.permutations(items):
        # Generate expressions for this permutation
        expressions = generate_all_expressions(list(perm))
        all_expressions.extend(expressions)
    
    # Remove duplicates
    return list(set(all_expressions))

def writef(path, content):
    with open(path, 'w') as f:
        f.write(content)

def main():
    # Example usage with items in the specified format
    items = ['{{0}}[0]', '{{0}}[1]', '{{0}}[2]', '{{0}}[3]']  # You can add more or remove items
    
    print(f"Generating all arithmetic expressions for items: {items}")
    
    expressions = generate_expressions_with_permutations(items)
    
    # Format expressions as a Python list string
    expressions_str = "[\n"
    for i, expr in enumerate(expressions):
        expressions_str += f"    \"{expr}\""
        if i < len(expressions) - 1:
            expressions_str += ",\n"
        else:
            expressions_str += "\n"
    expressions_str += "]\n"
    
    # Write to file
    file_path = "schemes/enum4"
    writef(file_path, expressions_str)
    
    print(f"\nTotal unique expressions: {len(expressions)}")
    print(f"Expressions written to {file_path}")

if __name__ == "__main__":
    main()