math_prompt = """
<Instruction> Calculate the given sequence. Output only number, no additional text. </Instruction>

<Examples>
Input: 86182889+89924248
Output: 176107137

Input: 3194277542452275+2348437648865245
Output: 5542715191317520

Input: 26792582327891974216653469162749+15683476524673487123131245651432
Output: 42476058852565461339784714814181
</Examples>

Input: {input}
"""

tot_improve_prompt = """
<Instruction> There are some errors in the following calculation sequence. Fine the errors in it and correct it. </Instruction>

<Approach>
To fix the incorrectly answer follow these steps:
1. Check all numbers in the sequence one by one.
2. Attention to the wrong digit addition
</Approach>

<Examples>
Input: 86182889+89924248
Incorrectly Answer: 176107127
Reason: Forget the first carry digit.
Output: 176107137

Input: 3194277542452275+2348437648865245
Incorrectly Answer: 5542715191317519
Reason: Wrong addition at the least significant digit
Output: 5542715191317520

Input: 26792582327891974216653469162749+15683476524673487123131245651432
Incorrectly Answer: 52476058852565461339784714814181
Reason: The incorrectly addition at the most significant digit
Output: 42476058852565461339784714814181
</Examples>

Input: {input}
Incorrectly Answer: {incorrectly_calculated}
"""

got_split_prompt = """
<Instruction> Split the following sequence of 8 numbers into 2 sequence of 4 numbers each, the first sequence should contain the first 4 numbers and the second sequence the second 4 numbers.
Only output the final 2 sequence in the following format without any additional text or thoughts!:
{{
    "sequence 1": 1234+6589,
    "sequence 2": 3563+9432
}} </Instruction>

<Example>
Input: 86182889+89924248
Output: 
{{
    "sequence 1": 8618+8992,
    "sequence 2": 2889+4248
}}
</Example>

Input: {input}
"""

got_merge_prompt = """
<Instruction> Merge the following 2 final answers.
Only output the final number without any additional text or thoughts!:</Instruction>

<Approach>
To merge the two number, follow these steps:
1. Concatenate two numbers
</Approach>

Merge the following two numbers into one answer:
1: {input1}
2: {input2}

Merged answer:
"""