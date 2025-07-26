import csv
import os
import nltk
import re
from nltk.tokenize import sent_tokenize, word_tokenize

# Download NLTK data if needed
nltk.download('punkt', quiet=True)

def prepare_divided_data():
    # Ensure directories exist
    os.makedirs('data/keyword', exist_ok=True)
    
    # Read the original complete data from div 1
    original_file = 'data/keyword/1.csv'
    rows = list(csv.reader(open(original_file)))
    
    # Process for div 2 and 4 (div 1 already exists)
    for div in ["2", "4"]:
        output_rows = []
        
        for row in rows:
            if len(row) < 3:
                continue
                
            idx = row[0]
            full_text = row[1]
            country_list_str = row[2]
            
            # Parse the country list from the original data
            original_countries = [c.strip() for c in country_list_str.strip('[]').split(',')]
            
            # Split the text into sentences
            sentences = sent_tokenize(full_text)
            total_sentences = len(sentences)
            
            # Determine how many sentences to keep
            if div == "2":
                keep_sentences = max(1, total_sentences // 2)
            elif div == "4":
                keep_sentences = max(1, total_sentences // 4)
            
            # Create the partial text
            partial_text = ' '.join(sentences[:keep_sentences])
            
            # Keep track of countries in the original order
            work_list = original_countries.copy()  # Copy to avoid modifying original
            partial_countries = []
            
            # Iterate through the partial text and match countries
            remaining_text = partial_text
            while remaining_text and work_list:
                next_country = work_list[0].strip()
                
                # Check if the next country appears at the start of the remaining text
                # Using regex with word boundaries to ensure proper matching
                pattern = r'\b' + re.escape(next_country) + r'\b'
                match = re.search(pattern, remaining_text)
                
                if match and match.start() == 0:
                    # Match found at the start, remove from work list and add to partial list
                    partial_countries.append(work_list.pop(0))
                    # Remove the matched text and continue
                    remaining_text = remaining_text[match.end():].lstrip()
                elif match:
                    # Match found but not at the start, move to the start of this match
                    remaining_text = remaining_text[match.start():]
                else:
                    # No match found, move to the next character
                    remaining_text = remaining_text[1:]
            
            partial_count = len(partial_countries)
            partial_length = len(partial_text)
            
            # Format the partial country list
            partial_countries_str = "[" + ", ".join(partial_countries) + "]"
            
            output_rows.append([idx, partial_text, partial_countries_str, str(partial_count), str(partial_length)])
        
        # Write the divided data to file
        output_file = f'data/keyword/{div}.csv'
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(output_rows)
        
        print(f"Created {output_file} with {len(output_rows)} rows")

if __name__ == "__main__":
    prepare_divided_data()