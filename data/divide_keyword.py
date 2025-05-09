import csv
import os
import nltk
from nltk.tokenize import sent_tokenize

# Download NLTK data if needed
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab')


def prepare_divided_data():
    # Ensure directories exist
    os.makedirs('data/keyword', exist_ok=True)
    
    # Read the original data
    original_file = 'data/keyword.csv'
    rows = list(csv.reader(open(original_file)))
    
    # Prepare data for each division
    for div in ["1", "2", "4"]:
        output_rows = []
        
        for row in rows:
            if len(row) < 3:
                continue
                
            idx = row[0]
            full_text = row[1]
            
            # Parse country list properly
            country_text = row[2].strip('[]').split(', ')
            all_countries = [c.strip() for c in country_text]
            
            count = row[3] if len(row) > 3 else len(all_countries)
            length = row[4] if len(row) > 4 else len(full_text)
            
            if div == "1":
                # Use the full text and all countries
                output_rows.append([idx, full_text, row[2], count, length])
            else:
                # Split text into sentences
                sentences = sent_tokenize(full_text)
                total_sentences = len(sentences)
                
                if div == "2":
                    keep_sentences = max(1, total_sentences // 2)
                elif div == "4":
                    keep_sentences = max(1, total_sentences // 4)
                
                # Keep only the first part of the text
                partial_text = ' '.join(sentences[:keep_sentences])
                
                # Determine which countries appear in this partial text
                partial_countries = []
                for country in all_countries:
                    if country in partial_text:
                        partial_countries.append(country)
                
                partial_count = len(partial_countries)
                partial_length = len(partial_text)
                
                # Format the partial country list like the original
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