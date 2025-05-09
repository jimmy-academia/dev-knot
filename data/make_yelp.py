import json
import csv
import random
import os
from collections import defaultdict

def load_yelp_reviews(file_path, max_reviews=1000):
    """
    Load a subset of reviews from the Yelp dataset
    
    Args:
        file_path: Path to the Yelp review dataset file
        max_reviews: Maximum number of reviews to load
    
    Returns:
        Dictionary with stars as keys and lists of reviews as values
    """
    reviews_by_stars = defaultdict(list)
    count = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if count >= max_reviews:
                break
            
            review = json.loads(line)
            
            # Only include reviews with stars 1 or 5 (negative or positive)
            if review['stars'] in [1, 5]:
                # Clean the text to remove potential CSV issues
                text = review['text'].replace('\n', ' ').replace('"', '""')
                reviews_by_stars[review['stars']].append(text)
                count += 1
    
    return reviews_by_stars

def create_query_instances(reviews_by_stars, num_instances, reviews_per_instance):
    """
    Create query instances with mixed positive and negative reviews
    
    Args:
        reviews_by_stars: Dictionary with stars as keys and lists of reviews as values
        num_instances: Number of query instances to create
        reviews_per_instance: Number of reviews per query instance
    
    Returns:
        List of tuples (reviews, num_positive)
    """
    query_instances = []
    
    positive_reviews = reviews_by_stars[5]
    negative_reviews = reviews_by_stars[1]
    
    for _ in range(num_instances):
        # Randomly decide how many positive reviews to include
        num_positive = random.randint(0, reviews_per_instance)
        num_negative = reviews_per_instance - num_positive
        
        # Ensure we have enough reviews
        if num_positive > len(positive_reviews) or num_negative > len(negative_reviews):
            continue
        
        # Sample reviews without replacement
        selected_positive = random.sample(positive_reviews, num_positive)
        selected_negative = random.sample(negative_reviews, num_negative)
        
        # Combine and shuffle
        all_reviews = selected_positive + selected_negative
        random.shuffle(all_reviews)
        
        query_instances.append((all_reviews, num_positive))
    
    return query_instances

def write_to_csv(query_instances, output_file):
    """
    Write query instances to a CSV file
    
    Args:
        query_instances: List of tuples (reviews, num_positive)
        output_file: Path to output CSV file
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'query', 'answer'])
        
        for i, (reviews, num_positive) in enumerate(query_instances):
            # Convert list of reviews to a string representation
            reviews_str = json.dumps(reviews)
            writer.writerow([i, reviews_str, num_positive])

def main():
    # Path to Yelp review dataset
    # This should be updated to the actual path of your Yelp dataset
    yelp_file_path = "/home/jimmyyeh/Documents/CRATER/DATASET/yelp/yelp_academic_dataset_review.json"
    
    # Create output directory if it doesn't exist
    output_dir = "yelp"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load reviews (adjust the max_reviews parameter as needed)
    print("Loading Yelp reviews...")
    reviews_by_stars = load_yelp_reviews(yelp_file_path, max_reviews=10000)
    
    # Create query instances with 20 reviews per instance
    print("Creating query instances with 20 reviews...")
    query_instances_20 = create_query_instances(reviews_by_stars, num_instances=100, reviews_per_instance=20)
    write_to_csv(query_instances_20, os.path.join(output_dir, "20.csv"))
    
    # Create query instances with 30 reviews per instance
    print("Creating query instances with 30 reviews...")
    query_instances_30 = create_query_instances(reviews_by_stars, num_instances=100, reviews_per_instance=30)
    write_to_csv(query_instances_30, os.path.join(output_dir, "30.csv"))
    
    print(f"Generated files saved in {output_dir} directory")

if __name__ == "__main__":
    main()