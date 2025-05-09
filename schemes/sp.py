import logging
from .base import BaseScheme
from .prompt_generator import generate_large_digit_prompt, generate_arithmetic_prompt, \
                              generate_set_intersection_prompt, generate_sorting_prompt, \
                              generate_keyword_counting_prompt, generate_yelp_prompt

large_digit_8_subquestions = ['Add the rightmost 4 digits (with carry)',
                            'Add the next 4 digits (with carry).',
                            'Add the leftmost digits if there is any carry in the previous step. If not, please report the leftmost digit.',
                            'What is the final sum after applying all carries?']

large_digit_16_subquestions = ['Add the rightmost 8 digits (with carry)',
                            'Add the next 8 digits (with carry).',
                            'Add the leftmost digits if there is any carry in the previous step. If not, please report the leftmost digit.',
                            'What is the final sum after applying all carries?']

large_digit_32_subquestions = ['Add the rightmost 16 digits (with carry)',
                            'Add the next 16 digits (with carry).',
                            'Add the leftmost digits if there is any carry in the previous step. If not, please report the leftmost digit.',
                            'What is the final sum after applying all carries?']

large_digit_8_examples = '''
You are performing large number addition step by step. Here is the current state:
57247728+67594862
Add the rightmost 4 digits (with carry).
Answer: 7728+4862=12590 (write 2590, carry 1)
Add the next 4 digits (with carry).
Answer: 5724+6759+1=12484 (write 2484, carry 1)
Add the leftmost digits if there is any carry in the previous step. If not, please report the leftmost digit.
Answer: 5+6+1=12 (write 12)
What is the final sum after applying all carries?
Answer: 124842590

96182879+89924243
Add the rightmost 4 digits (with carry).
Answer: 2879+4243=7122 (write 2590, carry 0)
Add the next 4 digits (with carry).
Answer: 9618+8992+0=18610 (write 8610, carry 1)
Add the leftmost digits if there is any carry in the previous step. If not, please report the leftmost digit.
Answer: 9+8+1=18 (write 18)
What is the final sum after applying all carries?
Answer: 186107122

17279983+88626422
Add the rightmost 4 digits (with carry).
Answer: 9983+6422=16405 (write 6405, carry 1)
Add the next 4 digits (with carry).
Answer: 1727+8862+1=10589 (write 0589, carry 1)
Add the leftmost digits if there is any carry in the previous step. If not, please report the leftmost digit.
Answer: 1+8+1=10 (write 10)
What is the final sum after applying all carries?
Answer: 105896405

'''

large_digit_16_examples = '''
You are performing large number addition step by step. Here is the current state:
5465458164972518+8654164596886757
Add the rightmost 8 digits (with carry).
Answer: 64972518+96886757 = 161859275 (write 61859275, carry 1)
Add the next 8 digits (with carry).
Answer: 54654581+86541645+1 = 141196227 (write 41196227, carry 1)
Add the leftmost digits if there is any carry in the previous step. If not, please report the leftmost digit.
Answer: 5+8+1 = 14 (write 14)
What is the final sum after applying all carries?
Answer: 14119622761859275

8755199127635222+2236918819671343
Add the rightmost 8 digits (with carry).
Answer: 27635222+19671343 = 47306565 (write 47306565, carry 0)
Add the next 8 digits (with carry).
Answer: 87551991+22369188+0 = 109921179 (write 09921179, carry 1)
Add the leftmost digits if there is any carry in the previous step. If not, please report the leftmost digit.
Answer: 8+2=10 (write 10)
What is the final sum after applying all carries?
Answer: 10992117947306565

5422658231225515+8947832771156916
Add the rightmost 8 digits (with carry).
Answer: 31225515+71156916 = 102382431 (write 02382431, carry 1)
Add the next 8 digits (with carry).
Answer: 54226582+89478327+1 = 143704910 (write 43704910, carry 1)
Add the leftmost digits if there is any carry in the previous step. If not, please report the leftmost digit.
Answer: 5+8+1=14 (write 14)
What is the final sum after applying all carries?
Answer: 14370491002382431

'''

large_digit_32_examples = '''
You are performing large number addition step by step. Here is the current state:
59842829133617473427166884252972+24873376371863371698982744892145
Add the rightmost 16 digits (with carry).
Answer: 3427166884252972+1698982744892145=5126149629145117 (write 5126149629145117, carry 0)
Add the next 16 digits (with carry).
Answer: 5984282913361747+2487337637186337+0=8471620550548084 (write 8471620550548084, carry 0)
Add the leftmost digits if there is any carry from the previous step. If not, please report the leftmost digit.
Answer: No carry from the previous step. (write 8)
What is the final sum after applying all carries?
Answer: 84716205505480845126149629145117

93175932767993469678298381845899+48577377367844884353713174238979
Add the rightmost 16 digits (with carry).
Answer: 9678298381845899+4353713174238979=14032011556084878 (write 4032011556084878, carry 1)
Add the next 16 digits (with carry).
Answer: 9317593276799346+4857737736784488+1=14175331013583835 (write 4175331013583835, carry 1)
Add the leftmost digits if there is any carry from the previous step. If not, please report the leftmost digit.
Answer: 9+4+1=14 (write 14)
What is the final sum after applying all carries?
Answer: 141753310135838354032011556084878

66835854695757239949896546915596+26827957892431343461898885399286
Add the rightmost 16 digits (with carry).
Answer: 9949896546915596+3461898885399286 = 13411795432314882 (write 3411795432314882, carry 1)
Add the next 16 digits (with carry).
Answer: 6683585469575723+2682795789243134+1 = 9366381258818858 (write 9366381258818858, carry 1)
Add the leftmost digits if there is any carry in the previous step. If not, please report the leftmost digit.
Answer: 6+2+1=9 (write 9)
What is the final sum after applying all carries?
Answer: 93663812588188583411795432314882

'''

all_arith_subquestions = ['Compute multiplication and division first.', 
                          'Then compute the addition and subtraction.',
                          'Round the sum to two decimal places.']

all_arith_8_solving_examples = '''
You are performing arithmetic step by step. Here is the current state:

5*5/5*4+8-8+3*9
Compute multiplication and division first.
Answer: 5*5/5*4 = 25/5*4 = 5*4 = 20; 3*9 = 27
Then compute the addition and subtraction.
Answer: 20+8-8+27 = 47
Round the sum to two decimal places.
Answer: 47.0

8-8+2+2+5+7+9+3
Compute multiplication and division first.
Answer: There is no multiplication or division in this problem.
Then compute the addition and subtraction.
Answer: 8-8+2+2+5+7+9+3 = 28
Round the sum to two decimal places.
Answer: 28

4+8/8+2-4*3*1-6
Compute multiplication and division first.
Answer: 8/8 = 1; 4*3*1 = 12
Then compute the addition and subtraction.
Answer: 4+1+2-12-6 = -11
Round the sum to two decimal places.
Answer: -11.0

'''

all_arith_16_solving_examples = '''
You are performing arithmetic step by step. Here is the current state:

2/9-3-4+6+4-9+8+8-4*5-7+2/1+6+7
Compute multiplication and division first.
Answer: 2/9 = 0.2222; 4*5 = 20; 2/1 = 2
Then compute the addition and subtraction.
Answer: 0.2222-3-4+6+4-9+8+8-20-7+2+6+7 = -1.7778
Round the sum to two decimal places.
Answer: -1.78

6+3/2*2+9+3+5+1*3-2-2-2-8-6+5+5
Compute multiplication and division first.
Answer: 3/2*2 = 3; 1*3 = 3
Then compute the addition and subtraction.
Answer: 6+3+9+3+5+3-2-2-2-8-6+5+5
Round the sum to two decimal places.
Answer: 19.0

3+9+8+8*6+7+7*5*6+9-3+8-9-9+5-1
Compute multiplication and division first.
Answer: 8*6 = 48; 7*5*6 = 210
Then compute the addition and subtraction.
Answer: 3+9+8+48+7+210+9-3+8-9-9+5-1
Round the sum to two decimal places.
Answer: 285

'''

all_arith_32_solving_examples = '''
You are performing arithmetic step by step. Here is the current state:

8-2/2/9+9*1/7/3*4+2/5-9+4*8+5+8+9+5+5-2+7/2-2+6-8+7+6+5+1+6*3+1
Compute multiplication and division first.
Answer: 2/2/9 = 0.1111; 9*1/7/3*4 = 1.7143; 2/5 = 0.4; 4*8 = 32; 7/2 = 3.5; 6*3 = 18
Then compute the addition and subtraction.
Answer: 8-0.1111+1.7143+0.4-9+32+5+8+9+5+5-2+3.5-2+6-8+7+6+5+1+18+1 = 100.5032
Round the sum to two decimal places.
Answer: 100.5

5+1+7+2+6/6-7/6+4+5+9+7-7-3+2/7+7/9+8*4-4-8*8-3-5-8+9/1*8-6-3*4
Compute multiplication and division first.
Answer: 6/6 = 1; 7/6 = 1.1667; 2/7 = 0.2857; 7/9 = 0.7778; 8*4 = 32; 8*8 = 64; 9/1*8 = 72; 3*4 = 12
Then compute the addition and subtraction.
Answer: 5+1+7+2+1-1.1667+4+5+9+7-7-3+0.2857+0.7778+32-4-64-3-5-8+72-6-12 = 32.8968
Round the sum to two decimal places.
Answer: 32.9

7-7+5+3-6-1/8+5+9-3+4+3+5-1+2+3+8-2/7/7-3*8/8+4+2+3-5/1-1+3*3+3
Compute multiplication and division first.
Answer: 1/8 = 0.125; 2/7/7 = 0.0408; 3*8/8 = 3; 5/1 = 5; 3*3 = 9
Then compute the addition and subtraction.
Answer: 7-7+5+3-6-0.125+5+9-3+4+3+5-1+2+3+8-0.0408-3+4+2+3-5-1+9+3 = 48.8342
Round the sum to two decimal places.
Answer: 48.83

'''

set_intersection_32_subquestions = ["Check the first 16 elements of both sets and list common elements.",
                                    "Check the remaining 16 elements of both sets and list common elements.",
                                    "What is the final intersection of the two sets?"]

set_intersection_64_subquestions = ["Check the first 32 elements of both sets and list common elements.",
                                    "Check the remaining 32 elements of both sets and list common elements.",
                                    "What is the final intersection of the two sets?"]

set_intersection_128_subquestions = ["Check the first 64 elements of both sets and list common elements.",
                                     "Check the remaining 64 elements of both sets and list common elements.",
                                     "What is the final intersection of the two sets?"]

set_intersection_32_examples = """
We will find the common elements between the two sets step by step. Here is the current state:

({11, 60, 1, 49, 21, 33, 14, 56, 54, 15, 23, 40, 45, 22, 7, 28, 20, 46, 51, 6, 34, 37, 3, 50, 17, 8, 25, 0, 35, 47, 18, 19},{31, 11, 4, 63, 38, 58, 59, 24, 61, 14, 32, 39, 27, 46, 48, 19, 52, 57, 50, 56, 3, 2, 53, 29, 5, 37, 62, 41, 36, 12, 49, 16})
Check the first 16 elements of both sets and list common elements.
Answer: {11, 14}

Check the remaining 16 elements of both sets and list common elements.
Answer: {3, 37, 50}

Cross-check the subsets and list the remaining common elements.
Answer: {19, 46, 49, 56}
        
What is the final intersection of the two sets?
Answer: {3, 11, 14, 19, 37, 46, 49, 50, 56}
"""

set_intersection_64_examples = '''
We will find the common elements between the two sets step by step. Here is the current state:

({42, 73, 86, 39, 85, 77, 69, 59, 43, 127, 121, 88, 109, 53, 70, 66, 25, 51, 34, 78, 45, 11, 40, 99, 68, 47, 49, 41, 101, 31, 24, 84, 36, 29, 118, 75, 3, 27, 30, 80, 125, 8, 37, 46, 90, 21, 60, 83, 19, 6, 95, 117, 87, 18, 100, 13, 22, 10, 110, 102, 35, 81, 17, 63}, {34, 49, 116, 106, 112, 23, 5, 80, 18, 62, 90, 54, 32, 103, 37, 43, 9, 25, 92, 16, 111, 79, 64, 91, 107, 58, 72, 94, 7, 60, 33, 14, 19, 104, 28, 74, 96, 76, 38, 52, 114, 50, 17, 0, 3, 100, 69, 98, 2, 1, 99, 12, 95, 97, 123, 4, 126, 124, 82, 27, 67, 57, 115, 46},{3, 17, 18, 19, 25, 27, 34, 37, 43, 46, 49, 60, 69, 80, 90, 95, 99, 100})
Check the first 32 elements of both sets and list common elements.
Answer: {34, 49, 43, 25}

Check the remaining 32 elements of both sets and list common elements.
Answer: {3, 17, 27, 37, 46, 60, 69, 80, 90, 95, 100}

Cross-check the subsets and list the remaining common elements.
Answer: {18, 19, 99}
        
What is the final intersection of the two sets?
Answer: {3, 17, 18, 19, 25, 27, 34, 37, 43, 46, 49, 60, 69, 80, 90, 95, 99, 100}
'''

set_intersection_128_examples = '''
We will find the common elements between the two sets step by step. Here is the current state:

({132, 75, 157, 25, 199, 202, 147, 109, 221, 110, 220, 251, 213, 11, 224, 101, 200, 170, 155, 71, 119, 122, 39, 1, 29, 113, 189, 212, 10, 219, 49, 28, 151, 40, 103, 8, 145, 214, 114, 91, 175, 107, 152, 163, 148, 246, 176, 181, 18, 106, 74, 115, 144, 0, 205, 121, 46, 234, 142, 223, 228, 162, 96, 97, 130, 156, 172, 241, 33, 186, 137, 150, 65, 161, 226, 116, 111, 12, 146, 38, 167, 4, 108, 169, 61, 93, 190, 252, 22, 31, 3, 9, 13, 35, 23, 141, 129, 198, 85, 84, 62, 158, 201, 67, 117, 59, 41, 191, 56, 90, 51, 227, 143, 83, 184, 174, 125, 98, 232, 238, 57, 225, 54, 179, 177, 237, 37, 95}, {27, 162, 187, 254, 128, 227, 2, 165, 143, 109, 140, 46, 160, 26, 139, 171, 42, 199, 207, 30, 205, 117, 213, 48, 40, 212, 185, 196, 197, 94, 136, 35, 229, 193, 36, 7, 15, 43, 4, 203, 142, 144, 49, 31, 240, 124, 116, 69, 37, 250, 95, 105, 103, 168, 126, 64, 73, 206, 24, 157, 135, 118, 34, 134, 45, 62, 153, 5, 47, 239, 216, 222, 80, 231, 102, 21, 57, 215, 149, 141, 236, 32, 188, 204, 194, 23, 233, 83, 154, 210, 159, 70, 202, 253, 20, 71, 166, 242, 221, 228, 78, 230, 29, 145, 147, 81, 104, 235, 66, 100, 131, 132, 244, 195, 68, 72, 53, 182, 79, 248, 3, 82, 211, 173, 180, 17, 77, 51})
Check the first 64 elements of both sets and list common elements.
Answer: {199, 213, 212, 40, 49, 103, 145, 144, 142, 157, 162}

Check the remaining 64 elements of both sets and list common elements.
Answer: {3, 23, 51, 57, 62, 83, 141}

Cross-check the subsets and list the remaining common elements.
Answer: {4, 29, 31, 35, 37, 46, 71, 95, 109, 116, 117, 132, 143, 202, 205, 221, 227, 228}
        
What is the final intersection of the two sets?
Answer: {3, 4, 23, 29, 31, 35, 37, 40, 46, 49, 51, 57, 62, 71, 83, 95, 103, 109, 116, 117, 132, 141, 142, 143, 144, 145, 147, 157, 162, 199, 202, 205, 212, 213, 221, 227, 228}
'''

sorting_subquestions = ['Split the list into two equal halves.',
                        'Sort each sublist in ascending order.',
                        'Merge the sorted sublists into a single sorted list.']

sorting_16_examples = '''
You are performing list sorting step by step. Here is the current state:

[9, 6, 6, 8, 1, 4, 1, 9, 7, 0, 7, 7, 7, 1, 7, 5]
Split the list into two equal halves.
Answer: [9, 6, 6, 8, 1, 4, 1, 9], [7, 0, 7, 7, 7, 1, 7, 5]
Sort each sublist in ascending order.
Answer: [1, 1, 4, 6, 6, 8, 9, 9], [0, 1, 5, 7, 7, 7, 7, 7]
Merge the sorted sublists into a single sorted list.
Answer: [0, 1, 1, 1, 4, 5, 6, 6, 7, 7, 7, 7, 7, 8, 9, 9]

[0, 1, 9, 7, 0, 0, 2, 5, 6, 9, 6, 3, 5, 9, 2, 3]
Split the list into two equal halves.
Answer: [0, 1, 9, 7, 0, 0, 2, 5], [6, 9, 6, 3, 5, 9, 2, 3]
Sort each sublist in ascending order.
Answer: [0, 0, 0, 1, 2, 5, 7, 9], [2, 3, 3, 5, 6, 6, 9, 9]
Merge the sorted sublists into a single sorted list.
Answer: [0, 0, 0, 1, 2, 2, 3, 3, 5, 5, 6, 6, 7, 9, 9, 9]

'''

sorting_32_examples = '''
You are performing list sorting step by step. Here is the current state:

[0, 0, 5, 9, 0, 7, 9, 9, 1, 2, 6, 1, 1, 9, 0, 1, 3, 5, 2, 3, 5, 6, 0, 2, 7, 4, 6, 2, 9, 7, 9, 5]
Split the list into two equal halves.
Answer: [0, 0, 5, 9, 0, 7, 9, 9, 1, 2, 6, 1, 1, 9, 0, 1], [3, 5, 2, 3, 5, 6, 0, 2, 7, 4, 6, 2, 9, 7, 9, 5]
Sort each sublist in ascending order.
Answer: [0, 0, 0, 0, 1, 1, 1, 1, 2, 5, 6, 7, 9, 9, 9, 9], [0, 2, 2, 2, 3, 3, 4, 5, 5, 5, 6, 6, 7, 7, 9, 9]
Merge the sorted sublists into a single sorted list.
Answer: [0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 4, 5, 5, 5, 5, 6, 6, 6, 7, 7, 7, 9, 9, 9, 9, 9, 9]

[5, 6, 2, 3, 1, 4, 9, 0, 5, 7, 0, 7, 1, 3, 2, 4, 5, 5, 6, 6, 3, 6, 4, 4, 2, 3, 7, 1, 7, 0, 2, 5]
Split the list into two equal halves.
Answer: [5, 6, 2, 3, 1, 4, 9, 0, 5, 7, 0, 7, 1, 3, 2, 4], [5, 5, 6, 6, 3, 6, 4, 4, 2, 3, 7, 1, 7, 0, 2, 5]
Sort each sublist in ascending order.
Answer: [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 7, 7, 9], [0, 1, 2, 2, 3, 3, 4, 4, 5, 5, 5, 6, 6, 6, 7, 7]
Merge the sorted sublists into a single sorted list.
Answer: [0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 9]

'''

sorting_64_examples = '''
You are performing list sorting step by step. Here is the current state:

[6, 3, 6, 5, 1, 2, 4, 3, 8, 0, 7, 8, 6, 4, 9, 5, 2, 4, 8, 4, 4, 4, 5, 6, 8, 4, 7, 7, 8, 9, 4, 9, 5, 4, 8, 4, 0, 5, 6, 9, 1, 2, 3, 6, 2, 0, 8, 1, 0, 7, 1, 2, 0, 7, 6, 9, 9, 9, 5, 6, 8, 3, 9, 0]
Split the list into two equal halves.
Answer: [6, 3, 6, 5, 1, 2, 4, 3, 8, 0, 7, 8, 6, 4, 9, 5, 2, 4, 8, 4, 4, 4, 5, 6, 8, 4, 7, 7, 8, 9, 4, 9], [5, 4, 8, 4, 0, 5, 6, 9, 1, 2, 3, 6, 2, 0, 8, 1, 0, 7, 1, 2, 0, 7, 6, 9, 9, 9, 5, 6, 8, 3, 9, 0]
Sort each sublist in ascending order.
Answer: [0, 1, 2, 2, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 8, 8, 8, 8, 8, 9, 9, 9], [0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4, 5, 5, 5, 6, 6, 6, 6, 7, 7, 8, 8, 8, 9, 9, 9, 9, 9]
Merge the sorted sublists into a single sorted list.
Answer: [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 9, 9]

'''

keyword_counting_subquestions = [
    "Identify the country names from the first portion of the text.",
    "Identify the country names from the next portion of the text.",
    "Continue identifying the country names from the next section.",
    "List any remaining country names from the final portion of the text.",
    "What is the final list of country names extracted?"
]

keyword_counting_example = '''
You are extracting country names from a given text.

One evening, Sarah, an archaeologist from Norway made a surprising discovery about ancient trade routes between Sweden and Norway. As per her research, the artifacts that were found in Norway were identical to those in Sweden, indicating a deep-rooted cultural connection between Sweden and Norway. This piqued the interest of her colleague, James, who was from Canada. He had been researching the indigenous tribes of Canada and found many similarities with tribes from his neighboring country, the United States. James had always been interested in the historical ties between Canada and United States, and his study further confirmed the age-old connections between the two countries. Upon hearing James's story, Sarah shared a fascinating anecdote from her travels in Portugal. She recalled how locals loved to tell the tale of the shared history between Spain and Portugal. Her anecdotes about Spain and Portugal echoed the same sense of shared culture and past, just like in the case of Norway and Sweden, and Canada and United States. Their conversation reminded James of his stay in South Korea, where he had learned about the close relationship between North Korea and South Korea, despite their current political divide. He recalled stories about the shared history of North Korea and South Korea, whose deep-seated cultural ties transcended political boundaries. Sarah, who had been to Australia, reciprocated with her own experiences of the bond between Australia and New Zealand. She described how, despite geographical separation, Australia and New Zealand shared a unique camaraderie and close historical ties. As they exchanged stories, their conversation moved to South Africa and its various connections with its neighbouring country, Zimbabwe. Sarah shared stories she had heard about the intricate bond between South Africa and Zimbabwe, showcasing the age-old interactions between these two nations. It left them both reflecting on the timeless bonds that connect nations across the world, from Norway to Australia, Canada to Zimbabwe, and all the countries in between.

Identify the country names from the first portion of the text.
One evening, Sarah, an archaeologist from Norway made a surprising discovery about ancient trade routes between Sweden and Norway. As per her research, the artifacts that were found in Norway were identical to those in Sweden, indicating a deep-rooted cultural connection between Sweden and Norway. This piqued the interest of her colleague, James, who was from Canada. He had been researching the indigenous tribes of Canada and found many similarities with tribes from his neighboring country, the United States.
Answer: [Norway, Sweden, Norway, Sweden, Sweden, Norway, Canada, United States]

Identify the country names from the next portion of the text.
James had always been interested in the historical ties between Canada and United States, and his study further confirmed the age-old connections between the two countries. Upon hearing James's story, Sarah shared a fascinating anecdote from her travels in Portugal. She recalled how locals loved to tell the tale of the shared history between Spain and Portugal. Her anecdotes about Spain and Portugal echoed the same sense of shared culture and past, just like in the case of Norway and Sweden, and Canada and United States. 
Answer: [Canada, United States, Portugal, Spain, Portugal, Spain, Portugal, Norway, Sweden, Canada, United States]

Continue identifying the country names from the next section.
Their conversation reminded James of his stay in South Korea, where he had learned about the close relationship between North Korea and South Korea, despite their current political divide. He recalled stories about the shared history of North Korea and South Korea, whose deep-seated cultural ties transcended political boundaries. Sarah, who had been to Australia, reciprocated with her own experiences of the bond between Australia and New Zealand. She described how, despite geographical separation, Australia and New Zealand shared a unique camaraderie and close historical ties.
Answer: [South Korea, North Korea, South Korea, North Korea, South Korea, Australia, Australia, New Zealand, Australia, New Zealand]

List any remaining country names from the final portion of the text.
As they exchanged stories, their conversation moved to South Africa and its various connections with its neighbouring country, Zimbabwe. Sarah shared stories she had heard about the intricate bond between South Africa and Zimbabwe, showcasing the age-old interactions between these two nations. It left them both reflecting on the timeless bonds that connect nations across the world, from Norway to Australia, Canada to Zimbabwe, and all the countries in between.
Answer: [South Africa, Zimbabwe, South Africa, Zimbabwe, Norway, Australia, Canada, Zimbabwe]

What is the final list of country names extracted?
Answer: [Norway, Sweden, Norway, Norway, Sweden, Sweden, Norway, Canada, Canada, United States, Canada, United States, Portugal, Spain, Portugal, Spain, Portugal, Norway, Sweden, Canada, United States, South Korea, North Korea, South Korea, North Korea, South Korea, Australia, Australia, New Zealand, Australia, New Zealand, South Africa, Zimbabwe, South Africa, Zimbabwe, Norway, Australia, Canada, Zimbabwe]

My friend, Alex from Peru, once recounted his journey to Argentina where he learned about the strong cultural ties between Argentina and Brazil due to their shared history. He spoke fondly of his time in Argentina and Brazil, marveling at the similar music, dance, and culinary traditions that seamlessly bridged the borders of these countries. 
It reminded me of a documentary I'd watched about the ancient Silk Road that spanned across Iran and China. It touched upon the shared historical narratives of Iran and China, highlighting how goods, ideas, and culture flowed between these two countries for centuries. Intriguingly, the documentary also brought up some parallels between this eastern route and the vibrant exchange between Italy and France during the Renaissance. The cultural and intellectual bonds between Italy and France were indeed profound, just as the resilient trade relations that existed between the United States and Canada. 
The United States and Canada, apart from their geographical proximity, shared an economic bond that strongly influenced their policies and international standing. Similarly, the ties between Australia and New Zealand shed light on their gestalt identity in the Pacific region. Despite their unique characteristics, Australia and New Zealand were often viewed as a single entity due to their remarkably similar backgrounds in terms of culture, language, and colonial history. Inspired by these chronicles of interconnectedness, I decided to delve deeper into history and found a fascinating account of how Ukraine and Poland had influenced each other through years of coexistence. 
Despite their tumultuous past, Ukraine and Poland shared a cultural tapestry that was deeply woven into their histories. It was quite similar to the complex relationship between North Korea and South Korea, which, despite their political differences, shared common heritage and traditions. Thus, from Argentina to South Korea, the world was an intricate web of countries intertwined with each other through shared histories, cultures, and sometimes, shared destinies.

Identify the country names from the first portion of the text.
My friend, Alex from Peru, once recounted his journey to Argentina where he learned about the strong cultural ties between Argentina and Brazil due to their shared history. He spoke fondly of his time in Argentina and Brazil, marveling at the similar music, dance, and culinary traditions that seamlessly bridged the borders of these countries. 
Answer: [Peru, Argentina, Argentina, Brazil, Argentina, Brazil]

Identify the country names from the next portion of the text.
It reminded me of a documentary I'd watched about the ancient Silk Road that spanned across Iran and China. It touched upon the shared historical narratives of Iran and China, highlighting how goods, ideas, and culture flowed between these two countries for centuries. Intriguingly, the documentary also brought up some parallels between this eastern route and the vibrant exchange between Italy and France during the Renaissance. The cultural and intellectual bonds between Italy and France were indeed profound, just as the resilient trade relations that existed between the United States and Canada. 
Answer: [Iran, China, Iran, China, Italy, France, Italy, France, United States, Canada]

Continue identifying the country names from the next section.
The United States and Canada, apart from their geographical proximity, shared an economic bond that strongly influenced their policies and international standing. Similarly, the ties between Australia and New Zealand shed light on their gestalt identity in the Pacific region. Despite their unique characteristics, Australia and New Zealand were often viewed as a single entity due to their remarkably similar backgrounds in terms of culture, language, and colonial history. Inspired by these chronicles of interconnectedness, I decided to delve deeper into history and found a fascinating account of how Ukraine and Poland had influenced each other through years of coexistence. 
Answer: [United States, Canada, Australia, New Zealand, Australia, New Zealand, Ukraine, Poland]

List any remaining country names from the final portion of the text.
Despite their tumultuous past, Ukraine and Poland shared a cultural tapestry that was deeply woven into their histories. It was quite similar to the complex relationship between North Korea and South Korea, which, despite their political differences, shared common heritage and traditions. Thus, from Argentina to South Korea, the world was an intricate web of countries intertwined with each other through shared histories, cultures, and sometimes, shared destinies.
Answer: [Ukraine, Poland, North Korea, South Korea, Argentina, South Korea]

What is the final list of country names extracted?
Answer: [Peru, Argentina, Argentina, Brazil, Argentina, Brazil, Iran, China, Iran, China, Italy, France, Italy, France, United States, Canada, United States, Canada, Australia, New Zealand, Australia, New Zealand, Ukraine, Poland, Ukraine, Poland, North Korea, South Korea, Argentina, South Korea]

'''

yelp_example = '''
We will analyze the given list of reviews and identify how many are positive.

['""After seeing the Mt. Vesuvious on Man vs. Food I became obsessed with the Franklin Fountain!  What a collossal dissapointment!""\n\nME TOO! It was also MUCH smaller than on TV - guess they made it special for him. It is WAY overpriced. I feel NO need to ever go back there. Just too expensive for ice cream.\n\n1 star because of the ridiculous prices.', 
""The best old-fashioned ice cream around. You may see the prices and freak out, but you get enormous scoops of ice cream here, so the price really isn't that bad. The ingredients are all-natural here: Actual chunks of peaches, strawberries, pieces of mint, even pieces of honeycomb in the honey ice cream! The atmosphere is great, and fits in with Old City really well. 90% of the time, you'll have to stand in line for this ice cream, but its worth it. If you love chocolate, I highly recommend the Whirly Berley."", 
""If you're gonna be Cash Only, then you need to do 2 things: first, get with the program; we're moving closer and closer to a cashless society...... You lost a sale tonight, and Im sure youve lost a lot more over time, because there are no working ATMs in your immediate area. Secondly, get a freakin ATM in your store to accomodate your potential customers, that you would lose otherwise! You make MORE money with MORE customers, whether its thru plastic or having your own ATM!!"", 
'Come on!  This place is over rated!  I had the mt. Vesuvius and it was ordinary!  Coldstones founders favorite is better than that!  I could have saved myself the $10 and gotten bryers ice cream and entenmans brownies and that would have been better.  The place is overly pretentious!  I would definitly not be going back!', 
""Haven't here is a while - total disappointment. One scoop of ice cream on a stale cone $6. Quality of ice cream has gone downhill. Used be creamer and richer. Hopefully they can come back"", 
""We came here on a frigid day in November. I got the peanut butter brownie sundae, and husband got a cone with 2 scoops. The scoops were really big. \n\nThe sundae was amaze! Super peanut buttery. And the brownies weren't just chopped up cheap cosmic brownies or something (no offense to a cosmic brownie - they have their place), they are warm, moist brownie pieces. Idk what could be better. \n\nIf I lived here, I'd go all the time to try all the different options (and be 128753784 pounds). They have lots of yummy looking sodas, floats and a lot of ice cream flavors, shakes and sundaes. \n\nYou order at the window and then pickup at a side window. Expect a few minute wait after you order, but it's worth it. You don't rush greatness."", 
""Maybe it's their Monday night crew or maybe this spot jumped the shark, but my experience last night was not the place I remember just a few years ago. It was staffed with all Gen Z'ers who felt really entitled for tips with the 3 or 4 tip jars you walked by while they struggled to simply scoop a small ice cream into a cone and make a crappy root beer float with a horrible ratio of soda to ice cream and charge  you $15 for it. Never again. Don't believe the hype!"", 
""Franklin Fountain has, without a doubt, the best ice cream and milkshakes I've ever eaten.\n\nMy favorite item on the menu (and I've tried a lot) is the Franklin Mint Shake, complete with homemade chocolate from Shane Confectionary (which has the same owners and is a couple doors down) as well as mint from Shane's rooftop, the result is a simultaneity decadent and refreshing milkshake.  The texture of the shake is perfect, frothy and milky but not too thin.  One of the best parts of the shake is when you reach the bottom, there's still lots of chocolate pieces to be enjoyed.\n\nOther shakes\\/ice cream flavors are also quite good.  The coconut ice cream is chock-full of fresh coconut flakes, making for a powerful and delicious flavor.  The Hydrox Cookie is full of chocolate and cream flavors, and also goes quite well in a shake.\n\nAs for sundaes, the Mount Vesuvius and the Franklin Mint are both delicious.  The Mount Vesuvius is a brownie fudge sundae and is supremely rich and delicious.  Brownies are freshly-baked an warm, as is the hot fudge.  Vanilla and chocolate ice cream are the perfect bases for this delicious sundae.  The Franklin Mint features vanilla bean ice cream, topped with hot fudge, crème de menthe sauce, and the same delicious chocolate in the mint shake.  It is great also.\n\nIn the winter, given the chilly temperatures in Philly, Franklin Fountain unveils an innovative and delicious Winter menu.  The S'mores hot milkshake on the winter menu is phenomenal.  This shake features vanilla bean ice cream mixed with  a warm, homemade graham cracker, homemade marshmallows flamed to toasty, and hot fudge.  The end result is a beautiful product that tastes like warm melting ice cream.  It is fantastic as all the flavors come together beautifully.\n\nFranklin may often have a wait, but it is completely worth waiting for every time for the outrageously good milkshakes and sundaes."", 
'Today I went to Franklin Fountain for the second time since moving to Philadelphia. While the ice cream is delicious, the experience I had today was far from satisfactory. After waiting in a very long line that extended outside the store and down the street, I finally reached the door. A woman walking along the street walked straight into the store, ignoring the line and cut right in front of me. \n\nAt first, we thought she was meeting someone who was holding a spot for her or in a rush to use the bathroom. When we noticed that this was not the case, my boyfriend said ""excuse me"" twice to the woman, who turned her back and ignored him. I got her attention and said ""excuse me ma\'am, but you\'ve just cut a very long line."" Her response was, ""I\'m deaf."" I repeated my comment to her loud enough that the entire staff could hear. The staff appropriately asked her if she had, indeed, cut the line, to which she responded, ""I\'m mentally ill. I have PTSD."" The staff offered to show her to the end of the line and she responded by saying, ""No, I just want ice cream."" \n\nIn the end, the woman was not forced to wait her turn, like all of the other customers had to, and she even signaled for a man outside to come cut the line with her.  She told him ""They said it\'s ok!"" and he too, rudely cut in front of me and everyone else. \n\nFranklin Fountain needs to learn to respect its customers and enforce common courtesy. I understand that the blame is really on this woman, but I am disappointed and offended that she and was still served. She may very well be mentally ill like she said, but she gives PTSD sufferers who understand how to wait in line a bad name.', 
""Hydrox cookie is the original Oreo! And the better looking one  so delicious! All their flavors taste on point and you can't go wrong. Love love this place. Their sister shop, Shane confectionery, has the best ice cream sandwiches. My favorite is the coconut almond cookie ice cream sandwich""]

Count the number of positive reviews in the first chunk.
['""After seeing the Mt. Vesuvious on Man vs. Food I became obsessed with the Franklin Fountain!  What a collossal dissapointment!""\n\nME TOO! It was also MUCH smaller than on TV - guess they made it special for him. It is WAY overpriced. I feel NO need to ever go back there. Just too expensive for ice cream.\n\n1 star because of the ridiculous prices.', 
""The best old-fashioned ice cream around. You may see the prices and freak out, but you get enormous scoops of ice cream here, so the price really isn't that bad. The ingredients are all-natural here: Actual chunks of peaches, strawberries, pieces of mint, even pieces of honeycomb in the honey ice cream! The atmosphere is great, and fits in with Old City really well. 90% of the time, you'll have to stand in line for this ice cream, but its worth it. If you love chocolate, I highly recommend the Whirly Berley.""]
Answer: 1

Count the number of positive reviews in the second chunk.
[""If you're gonna be Cash Only, then you need to do 2 things: first, get with the program; we're moving closer and closer to a cashless society...... You lost a sale tonight, and Im sure youve lost a lot more over time, because there are no working ATMs in your immediate area. Secondly, get a freakin ATM in your store to accomodate your potential customers, that you would lose otherwise! You make MORE money with MORE customers, whether its thru plastic or having your own ATM!!"", 
'Come on!  This place is over rated!  I had the mt. Vesuvius and it was ordinary!  Coldstones founders favorite is better than that!  I could have saved myself the $10 and gotten bryers ice cream and entenmans brownies and that would have been better.  The place is overly pretentious!  I would definitly not be going back!', 
""Haven't here is a while - total disappointment. One scoop of ice cream on a stale cone $6. Quality of ice cream has gone downhill. Used be creamer and richer. Hopefully they can come back""]
Answer: 1

Count the number of positive reviews in the third chunk.
[""We came here on a frigid day in November. I got the peanut butter brownie sundae, and husband got a cone with 2 scoops. The scoops were really big. \n\nThe sundae was amaze! Super peanut buttery. And the brownies weren't just chopped up cheap cosmic brownies or something (no offense to a cosmic brownie - they have their place), they are warm, moist brownie pieces. Idk what could be better. \n\nIf I lived here, I'd go all the time to try all the different options (and be 128753784 pounds). They have lots of yummy looking sodas, floats and a lot of ice cream flavors, shakes and sundaes. \n\nYou order at the window and then pickup at a side window. Expect a few minute wait after you order, but it's worth it. You don't rush greatness."", 
""Maybe it's their Monday night crew or maybe this spot jumped the shark, but my experience last night was not the place I remember just a few years ago. It was staffed with all Gen Z'ers who felt really entitled for tips with the 3 or 4 tip jars you walked by while they struggled to simply scoop a small ice cream into a cone and make a crappy root beer float with a horrible ratio of soda to ice cream and charge  you $15 for it. Never again. Don't believe the hype!"", 
""Franklin Fountain has, without a doubt, the best ice cream and milkshakes I've ever eaten.\n\nMy favorite item on the menu (and I've tried a lot) is the Franklin Mint Shake, complete with homemade chocolate from Shane Confectionary (which has the same owners and is a couple doors down) as well as mint from Shane's rooftop, the result is a simultaneity decadent and refreshing milkshake.  The texture of the shake is perfect, frothy and milky but not too thin.  One of the best parts of the shake is when you reach the bottom, there's still lots of chocolate pieces to be enjoyed.\n\nOther shakes\\/ice cream flavors are also quite good.  The coconut ice cream is chock-full of fresh coconut flakes, making for a powerful and delicious flavor.  The Hydrox Cookie is full of chocolate and cream flavors, and also goes quite well in a shake.\n\nAs for sundaes, the Mount Vesuvius and the Franklin Mint are both delicious.  The Mount Vesuvius is a brownie fudge sundae and is supremely rich and delicious.  Brownies are freshly-baked an warm, as is the hot fudge.  Vanilla and chocolate ice cream are the perfect bases for this delicious sundae.  The Franklin Mint features vanilla bean ice cream, topped with hot fudge, crème de menthe sauce, and the same delicious chocolate in the mint shake.  It is great also.\n\nIn the winter, given the chilly temperatures in Philly, Franklin Fountain unveils an innovative and delicious Winter menu.  The S'mores hot milkshake on the winter menu is phenomenal.  This shake features vanilla bean ice cream mixed with  a warm, homemade graham cracker, homemade marshmallows flamed to toasty, and hot fudge.  The end result is a beautiful product that tastes like warm melting ice cream.  It is fantastic as all the flavors come together beautifully.\n\nFranklin may often have a wait, but it is completely worth waiting for every time for the outrageously good milkshakes and sundaes.""]
Answer: 1

Count the number of positive reviews in the last chunk.
['Today I went to Franklin Fountain for the second time since moving to Philadelphia. While the ice cream is delicious, the experience I had today was far from satisfactory. After waiting in a very long line that extended outside the store and down the street, I finally reached the door. A woman walking along the street walked straight into the store, ignoring the line and cut right in front of me. \n\nAt first, we thought she was meeting someone who was holding a spot for her or in a rush to use the bathroom. When we noticed that this was not the case, my boyfriend said ""excuse me"" twice to the woman, who turned her back and ignored him. I got her attention and said ""excuse me ma\'am, but you\'ve just cut a very long line."" Her response was, ""I\'m deaf."" I repeated my comment to her loud enough that the entire staff could hear. The staff appropriately asked her if she had, indeed, cut the line, to which she responded, ""I\'m mentally ill. I have PTSD."" The staff offered to show her to the end of the line and she responded by saying, ""No, I just want ice cream."" \n\nIn the end, the woman was not forced to wait her turn, like all of the other customers had to, and she even signaled for a man outside to come cut the line with her.  She told him ""They said it\'s ok!"" and he too, rudely cut in front of me and everyone else. \n\nFranklin Fountain needs to learn to respect its customers and enforce common courtesy. I understand that the blame is really on this woman, but I am disappointed and offended that she and was still served. She may very well be mentally ill like she said, but she gives PTSD sufferers who understand how to wait in line a bad name.', 
""Hydrox cookie is the original Oreo! And the better looking one  so delicious! All their flavors taste on point and you can't go wrong. Love love this place. Their sister shop, Shane confectionery, has the best ice cream sandwiches. My favorite is the coconut almond cookie ice cream sandwich""]
Answer: 1

Summarize the total number of positive reviews at the end.
Answer: 4

'''

yelp_subquestions = ['Count the number of positive reviews in the first chunk',
                     'Count the number of positive reviews in the second chunk',
                     'Count the number of positive reviews in the third chunk',
                     'Count the number of positive reviews in the last chunk',
                     'Summarize the total number of positive reviews at the end.']

subquestion_dict = {'large_digit':{'8':large_digit_8_subquestions,'16':large_digit_16_subquestions,'32':large_digit_32_subquestions},
                    'all_arith':all_arith_subquestions,
                    'set_intersection':{'032':set_intersection_32_subquestions, '064':set_intersection_64_subquestions, '128':set_intersection_128_subquestions},
                    'sorting':{'016':sorting_subquestions,'032':sorting_subquestions,'064':sorting_subquestions},
                    'keyword_counting':keyword_counting_subquestions,
                    'yelp':yelp_subquestions}

Task_Specific_Example = {'large_digit':{'8':large_digit_8_examples,'16':large_digit_16_examples,'32':large_digit_32_examples},
                         'all_arith':{'08':all_arith_8_solving_examples,'16':all_arith_16_solving_examples,'32':all_arith_32_solving_examples},
                         'set_intersection':{'032':set_intersection_32_examples,'064':set_intersection_64_examples,'128':set_intersection_128_examples},
                         'sorting':{'016':sorting_16_examples,'032':sorting_32_examples,'064':sorting_64_examples},
                         'keyword_counting':keyword_counting_example,
                         'yelp':yelp_example}

def get_text_chunks(text):
    chunks = [
                text[:400],  # First chunk
                text[400:800],  # Second chunk
                text[800:1200],  # Third chunk
                text[1200:]  # Last chunk
             ]
    return chunks

def get_review_chunks(reviews):
    chunks = [
                (reviews[:2]),  # First chunk
                (reviews[2:4]),  # Second chunk
                (reviews[4:6]),  # Third chunk
                (reviews[6:])  # Last chunk
             ]
    return chunks

class Successive(BaseScheme):    
    def prep_const_prompt(self):
        if self.args.task == 'large_digit' or self.args.task == 'all_arith':
            successive_prompt = 'To compute %s, the next question to answer is:'
        if self.args.task == 'set_intersection': 
            successive_prompt = 'To find the intersection of sets %s, the next question to answer is:'
        if self.args.task == 'sorting':
            successive_prompt = 'To find the sorting result of list %s, the next question to answer is:'
        if self.args.task == 'keyword_counting':
            successive_prompt = 'To find the list of countries occurred in the paragraph %s, the next question to answer is:'
        if self.args.task == 'yelp':
            successive_prompt = 'To count the number of positive reviews from the review list %s, the next question to answer is:'
        return successive_prompt

    def prep_task_spcefics(self):
        if self.args.div:
            successive_solving_example = Task_Specific_Example.get(self.args.task).get(self.args.div)
        else:
            successive_solving_example = Task_Specific_Example.get(self.args.task)
        
        if self.args.task == 'large_digit' or self.args.task == 'set_intersection':
            succ_steps = 4
        elif self.args.task == 'all_arith' or self.args.task == 'sorting':
            succ_steps = 3
        else:
            succ_steps = 5
        return successive_solving_example, succ_steps
    
    def context_initializer(self, example, query):
        successive_prompt = self.prep_const_prompt()
        context = example + successive_prompt % str(query)
        return context
    
    def generate_prompt(self, question, context, text=None):
        if self.args.task == 'large_digit':
            prompt = generate_large_digit_prompt(question, context)
        if self.args.task == 'all_arith':
            prompt = generate_arithmetic_prompt(question, context)
        if self.args.task == 'set_intersection':
            prompt = generate_set_intersection_prompt(question, context)
        if self.args.task == 'sorting':
            prompt = generate_sorting_prompt(question, context)
        if self.args.task == 'keyword_counting':
            prompt = generate_keyword_counting_prompt(question, context, text)
        if self.args.task == 'yelp':
            prompt = generate_yelp_prompt(question, context, text)
        return prompt
    
    def solve_query(self, query):
        successive_solving_example, succ_steps = self.prep_task_spcefics()
        context = self.context_initializer(successive_solving_example, query)
        for i in range(succ_steps):
            question = self.llm_answer(context)
            context += question
            answer = self.llm_answer(context)
            print(f"Q: {question}\nA: {answer}\n")
            if i != succ_steps-1:
                context += f'\nFor question {question}, we already know the answer is {answer}.\nThe next question to answer is: '
            else:
                context += f'There are no more questions left to ask. The answer is {answer}.'
        
        if self.args.task == 'large_digit' or self.args.task == 'all_arith' or self.args.task == 'yelp':
            output = self.llm_answer("extract the numerical of the answer:"+answer)
        elif self.args.task == 'set_intersection':
            # answer = answer.split(', ')
            # output = [int(o) for o in answer]
            output = self.llm_answer(f"extract the set form of the answer:{answer}")
        elif self.args.task == 'sorting' or self.args.task == 'keyword_counting':
            output = self.llm_answer(f"extract the list form of the answer:{answer}")
        
        logging.info(f'>>>>>>>>>>>> final result: {output} <<<<<<<<<<<<<')
        return output