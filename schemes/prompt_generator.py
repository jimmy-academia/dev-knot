def generate_large_digit_prompt(question, context):
    return f"""
You are performing large number addition step by step. Here is the current state:

{context}

{question}

Answer:
"""

def generate_arithmetic_prompt(question, context):
    return f"""
You are performing arithmetic step by step. Here is the current state:

{context}

{question}

Answer:
"""

def generate_set_intersection_prompt(question, context):
    return f"""
We will find the common elements between the two sets step by step. Here is the current state:

{context}

{question}

Answer:
"""

def generate_sorting_prompt(question, context):
    return f"""
You are performing list sorting step by step. Here is the current state:

{context}

{question}

Answer:
"""

def generate_keyword_counting_prompt(question, context, text=None):
    if text is not None:
        return f"""You are extracting country names from a given text.

        {text}

        {context}

        {question}

        Answer:
        """
    else:
        return f"""You are extracting country names 
        {context}

        {question}

        Answer:
        """

# Define prompt template
def generate_yelp_prompt(question, context, review_chunk):
    return f"""We will analyze the given reviews and identify how many are positive.

Reviews:
{review_chunk}

{context}

{question}

Answer:
"""