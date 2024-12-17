add_prompt = """
<Instruction> Justify the following review is positive tone or negative tone. </Instruction>

<Examples>
Input: A menu that satisfies everyone's cravings! Clean, trendy, and delicious! I definitely recommend going early (before 9 am) as the wait tends to get longer after 9 am! But honestly, it is soooo worth the wait. You will leave there feeling so incredible satisfied!
Output: Positive

Input: I am a long term frequent customer of this establishment. I just went in to order take out (3 apps) and was told they're too busy to do it. Really? The place is maybe half full at best. Does your dick reach your ass? Yes? Go fuck yourself! I'm a frequent customer AND great tipper. Glad that Kanella just opened. NEVER going back to dmitris!
Output: Negative
</Examples>

Input: {seq}
"""

tot_improve_prompt = """
<Instruction> There are some errors in the following justification. Fine the errors in it and correct it. </Instruction>

<Examples>
Input: I am a long term frequent customer of this establishment. I just went in to order take out (3 apps) and was told they're too busy to do it. Really? The place is maybe half full at best. Does your dick reach your ass? Yes? Go fuck yourself! I'm a frequent customer AND great tipper. Glad that Kanella just opened. NEVER going back to dmitris!
Incorrectly Answer: Positive
Reason: The keyword is "never go back"
Output: Negative

Input: A menu that satisfies everyone's cravings! Clean, trendy, and delicious! I definitely recommend going early (before 9 am) as the wait tends to get longer after 9 am! But honestly, it is soooo worth the wait. You will leave there feeling so incredible satisfied!
Incorrectly Answer: Negative
Reason: The keyword is "satisfies everyone's cravings", "Clean, trendy, and delicious"
Output: Positive
</Examples>

Input: {input}
Incorrectly Answer: {incorrectly_calculated}
"""

split_prompt = """
<Instruction> Split the following array of 10 reviews into separate reviews.
Only output the separate reviews in the following format without any additional text or thoughts!:
"Review 1": ...,
"Review 2": ...,
...
"Review 10": ...
</Instruction>

Input: {seq}
"""

merge_prompt = """
<Instruction> Calculate how many positive in the following array
Only output the final number without any additional text or thoughts!:</Instruction>

<Approach>
Calculate how many positive in the input clearly.
</Approach>

Calculate how many positive in the following:
{input}

Answer:
"""
