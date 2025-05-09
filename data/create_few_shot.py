import json
import csv
import random
import os
from collections import defaultdict

def create_few_shot_examples(csv_paths, num_examples=3):
    """
    Create few-shot examples for different division sizes
    
    Args:
        csv_paths: Dictionary mapping division sizes to CSV file paths
        num_examples: Number of examples to create for each division
    
    Returns:
        Dictionary with division sizes as keys and lists of (example, answer) tuples as values
    """
    examples_by_division = {}
    
    for division_size, csv_path in csv_paths.items():
        if not os.path.exists(csv_path):
            print(f"Warning: File {csv_path} not found. Skipping division size {division_size}.")
            continue
            
        examples = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            rows = list(reader)
            # Select random rows if we have more than we need
            if len(rows) > num_examples:
                selected_rows = random.sample(rows, num_examples)
            else:
                selected_rows = rows
            
            for row in selected_rows:
                print(row)
                input()
                _, query_json, answer = row
                query = json.loads(query_json)
                # Format the example as needed
                examples.append((query, int(answer)))
        
        examples_by_division[division_size] = examples
    
    return examples_by_division

def format_example_for_prompt(example, answer, max_reviews_to_show=3):
    """
    Format a single example for use in a prompt
    
    Args:
        example: List of review strings
        answer: The correct answer (number of positive reviews)
        max_reviews_to_show: Maximum number of reviews to include in the formatted output
    
    Returns:
        Formatted example string
    """
    # Show only a subset of reviews to keep the prompt manageable
    shown_reviews = example[:max_reviews_to_show]
    total_reviews = len(example)
    
    formatted = f"Example (showing {max_reviews_to_show} of {total_reviews} reviews):\n"
    formatted += "  Query: [\n"
    
    for i, review in enumerate(shown_reviews):
        # Truncate long reviews
        if len(review) > 200:
            review = review[:200] + "..."
        
        formatted += f'    "{review}"'
        if i < len(shown_reviews) - 1:
            formatted += ",\n"
        else:
            formatted += f"\n    ... ({total_reviews - max_reviews_to_show} more reviews)\n"
    
    formatted += "  ]\n"
    formatted += f"  Answer: {answer}\n"
    
    return formatted

def print_few_shot_examples(examples_by_division):
    """
    Print few-shot examples for different division sizes
    
    Args:
        examples_by_division: Dictionary with division sizes as keys and 
                             lists of (example, answer) tuples as values
    """
    for division_size, examples in examples_by_division.items():
        print(f"\n{'='*80}")
        print(f"FEW-SHOT EXAMPLES FOR {division_size} REVIEWS PER QUERY")
        print(f"{'='*80}\n")
        
        for i, (example, answer) in enumerate(examples):
            print(f"Example {i+1}:")
            print(format_example_for_prompt(example, answer))
            print("-" * 40)

def main():
    # Define paths to CSV files for different division sizes
    csv_paths = {
        10: "data/yelp/10.csv",  # If you have this
        20: "data/yelp/20.csv",
        30: "data/yelp/30.csv"
    }
    
    # Create examples
    examples_by_division = create_few_shot_examples(csv_paths, num_examples=3)
    
    # Print examples
    print_few_shot_examples(examples_by_division)
    
    # You could also save these to a JSON file for later use
    with open("yelp_few_shot_examples.json", "w", encoding="utf-8") as f:
        # We need to convert the examples to a serializable format
        serializable_examples = {}
        for division, examples in examples_by_division.items():
            serializable_examples[division] = [
                {"example": ex, "answer": ans} for ex, ans in examples
            ]
        json.dump(serializable_examples, f, indent=2)
    
    print("\nFew-shot examples have been saved to yelp_few_shot_examples.json")

if __name__ == "__main__":
    main()