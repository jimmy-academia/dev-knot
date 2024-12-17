add_prompt = """
<Instruction> Calculate the sum of all numbers. Output only the number, no additional text. </Instruction>

<Examples>
Input: 5+1+0+1+2+0+4+8+3+2+7+6
Output: 39

Input: 3+7+0+2+8+1+2+2+5+8+2+5
Output: 45
</Examples>

Input: {seq}
"""

tot_improve_prompt = """
<Instruction> There are some errors in the following calculation sequence. Fine the errors in it and correct it. </Instruction>

<Approach>
To fix the incorrectly answer follow these steps:
1. Check all numbers in the sequence one by one.
</Approach>

<Examples>
Input: 3+5+6+2+4+5+3+2
Incorrectly Answer: 32
Reason: Add 2 one more time
Output: 30

Input: 7+4+7+6+7+3+7+2+7+7+3+3+6+2+5+4
Incorrectly Answer: 73
Reason: Forget to add 7, the fifth number in the sequence
Output: 80

Input: 7+6+2+7+3+6+5+2+4+2+4+7+2+4+3+3+3+5+4+7+6+4+6+7+6+5+2+7+7+3+7+7
Incorrectly Answer: 139
Reason: Forget to add the last two 7 in the sequence
Output: 153
</Examples>

Input: {input}
Incorrectly Answer: {incorrectly_calculated}
"""

split_prompt = """
<Instruction> Split the following Sequencce of 24 numbers into 2 Sequencces of 12 numbers each, the first Sequencce should contain the first 16 numbers and the second Sequencce the second 16 numbers.
Only output the final 2 Sequencces in the following format without any additional text or thoughts!:
"Sequencce 1": 3+4+2+5+...,
"Sequencce 2": 2+9+4+3+...
</Instruction>

<Example>
Input: 9+6+7+7+6+3+7+4+2+4+7+8+1+3+4+2+3+5+4+6+2+5+7+9
Output:
"Sequencce 1": 9+6+7+7+6+3+7+4+2+4+7+8,
"Sequencce 2": 1+3+4+2+3+5+4+6+2+5+7+9
</Example>

Input: {seq}
"""

merge_prompt = """
<Instruction> Add 2 number.
Only output the final number without any additional text or thoughts!:</Instruction>

<Approach>
Add 2 number
</Approach>

Add the following two number:
1: {seq1}
2: {seq2}

Answer:
"""
