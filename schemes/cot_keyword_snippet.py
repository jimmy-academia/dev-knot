    'keyword': """Input: One evening, Sarah, an archaeologist from Norway made a surprising discovery about ancient trade routes between Sweden and Norway. As per her research, the artifacts that were found in Norway were identical to those in Sweden, indicating a deep-rooted cultural connection between Sweden and Norway. This piqued the interest of her colleague, James, who was from Canada.
Context: Output all words about countries in the article. You can seperate article into sentences first. The maximum number of sentences is 20.

Let's think step by step

Output:
Sentence 1: "One evening, Sarah, an archaeologist from Norway made a surprising discovery about ancient trade routes between Sweden and Norway." -> Norway, Sweden, Norway
Sentence 2: "As per her research, the artifacts that were found in Norway were identical to those in Sweden, indicating a deep-rooted cultural connection between Sweden and Norway." -> Norway, Sweden, Sweden, Norway
Sentence 3: "This piqued the interest of her colleague, James, who was from Canada." -> Canada

Combined List: [Norway, Sweden, Norway, Norway, Sweden, Sweden, Norway, Canada]

Final answer: [Norway, Sweden, Norway, Norway, Sweden, Sweden, Norway, Canada]

Input: {query}
Context: Output all words about countries in the article. You can seperate article into sentences first. The maximum number of sentences is 20. Format: [Country1, Country2, ...]. Include ALL occurrences (keep duplicates). Absolutely NO quotes.

Let's think step by step

Output:""",
