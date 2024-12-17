math_prompt = """
<Instruction> Calculate the given sequence. Output only number, no additional text. </Instruction>

<Examples>
Input: 3+5+6+2+4+5*3+2
Output: 37

Input: 7+4+7*6+7+3+7+2+7*7+3+3*6+2+5+4
Output: 153

Input: 7+6+2+7+3+6+5*2+4+2+4+7+2+4+3*3+3+5+4+7+6+4+6+7+6+5*2*7+7+3+7+7
Output: 215
</Examples>

Input: {input}
"""

tot_improve_prompt = """
<Instruction> There are some errors in the following calculation sequence. Fine the errors in it and correct it. </Instruction>

<Approach>
To fix the incorrectly answer follow these steps:
1. Check all numbers in the sequence one by one.
2. Attention to the symbol error using.
</Approach>

<Examples>
Input: 3+5+6+2+4+5*3+2
Incorrectly Answer: 39
Reason: Add 2 one more time
Output: 37

Input: 7+4+7*6+7+3+7+2+7*7+3+3*6+2+5+4
Incorrectly Answer: 149
Reason: Forget to add 4, the last number in the sequence
Output: 153

Input: 7+6+2+7+3+6+5*2+4+2+4+7+2+4+3*3+3+5+4+7+6+4+6+7+6+5*2*7+7+3+7+7
Incorrectly Answer: 202
Reason: The incorrectly addition of the first two numbers, remember to add.
Output: 215
</Examples>

Input: {input}
Incorrectly Answer: {incorrectly_calculated}
"""

got_split_prompt = """
<Instruction> Split the following sequence of 8 numbers into 2 sequence of 4 numbers each, the first sequence should contain the first 4 numbers and the second sequence the second 4 numbers.
Only output the final 2 sequence in the following format without any additional text or thoughts!:
{{
    "sequence 1": 3+4+5*1,
    "sequence 2": 5+2+3*4
}} </Instruction>

<Example>
Input: 3+5+6+2+4+5*3+2
Output: 
{{
    "sequence 1": 3+5+6+2,
    "sequence 2": 4+5*3+2
}}
</Example>

Input: {input}
"""

got_merge_prompt = """
<Instruction> Merge the following 2 final answers.
Only output the final number without any additional text or thoughts!:</Instruction>

<Approach>
To merge the two number, follow these steps:
1. Calculate the answer of 2 numbers
</Approach>

Merge the following two numbers into one answer:
1: {input1}
2: {input2}

Merged answer:
"""