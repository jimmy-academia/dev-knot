import random
import logging
from .base import BaseScheme
from collections import Counter


ContextPrompts = {
    'healthcare': 'We want to determine the correct treatment based on the workflow.',
    'keyword': 'We are extracting every occurrence of country names, preserving duplicates and maintaining their original order in the paragraph: ',
    'yelp': 'We are counting the number of positive reviews from the review list: ',
    'addition': 'We are calculating the arithmetic result of input sequence: ',
    'arithmetic': 'We are calculating the arithmetic result of input sequence: ',
    'gsm8k': 'We are solving the math problems and adding up the answers to give the final answer.'
}
Task_Specific_Example = {
    'addition': """Input: 8+2+7+3+5+5+1+9

Let's think step by step

Output:
8+2+7+3+5+5+1+9
10+7+3+5+5+1+9
17+3+5+5+1+9
20+5+5+1+9
25+5+1+9
30+1+9
31+9
40

Final answer: 40

Input: 3+7+5+2+8+1+6+4

Let's think step by step

Output:
3+7+5+2+8+1+6+4
10+5+2+8+1+6+4
15+2+8+1+6+4
17+8+1+6+4
25+1+6+4
26+6+4
32+4
36

Final answer: 36

Input: 5+3+9+1+7+2+8+6

Let's think step by step

Output:
5+3+9+1+7+2+8+6
8+9+1+7+2+8+6
17+1+7+2+8+6
18+7+2+8+6
25+2+8+6
27+8+6
35+6
41

Final answer: 41

Input: {query}

Let's think step by step. 

Output:""",
    'arithmetic': """Input: 8+2*7-3*5+5/1+9

Let's think step by step

Output:
8+2*7-3*5+5/1+9
8+14-3*5+5/1+9
22-3*5+5/1+9
22-15+5/1+9
7+5/1+9
7+5+9
12+9
21

Final answer: 21

Input: 3+7-5+2*8*1-6/4

Let's think step by step

Output:
3+7-5+2*8*1-6/4
10-5+2*8*1-6/4
5+2*8*1-6/4
5+16*1-6/4
5+16-6/4
21-6/4
21-1.5
19.5

Final answer: 19.5

Input: 5*9/3-1+7*2-8+6

Let's think step by step

Output:
5*9/3-1+7*2-8+6
45/3-1+7*2-8+6
15-1+7*2-8+6
14+7*2-8+6
14+14-8+6
28-8+6
20+6
26

Final answer: 26

Input: {query}

Let's think step by step. 

Output:""",
    'yelp': """Input: [REVIEW_1] A menu that satisfies everyone's cravings! Clean, trendy, and delicious! I definitely recommend going early (before 9 am) as the wait tends to get longer after 9 am! But honestly, it is soooo worth the wait. You will leave there feeling so incredible satisfied! [REVIEW_2] I am a long term frequent customer of this establishment. I just went in to order take out (3 apps) and was told they're too busy to do it. Really? The place is maybe half full at best. Does your dick reach your ass? Yes? Go fuck yourself! I'm a frequent customer AND great tipper. Glad that Kanella just opened. NEVER going back to dmitris!

Let's think step by step. 

Output: 
[REVIEW_1] A menu that satisfies everyone's cravings! Clean, trendy, and delicious! I definitely recommend going early (before 9 am) as the wait tends to get longer after 9 am! But honestly, it is soooo worth the wait. You will leave there feeling so incredible satisfied! 
this is a positive review
[REVIEW_2] I am a long term frequent customer of this establishment. I just went in to order take out (3 apps) and was told they're too busy to do it. Really? The place is maybe half full at best. Does your dick reach your ass? Yes? Go fuck yourself! I'm a frequent customer AND great tipper. Glad that Kanella just opened. NEVER going back to dmitris!
this is a not a positive review

Final answer: the number of positive review is 1

Input: [REVIEW_1] The pasta was amazing and the service was excellent! [REVIEW_2] The food was great but the service was terrible. [REVIEW_3] I love this place and will definitely come back!

Let's think step by step. 

Output:
[REVIEW_1] The pasta was amazing and the service was excellent! 
this is a positive review
[REVIEW_2] The food was great but the service was terrible. 
this is a not a positive review
[REVIEW_3] I love this place and will definitely come back!
this is a a positive review

Final answer: the number of positive review is 2

Input: {query}

Let's think step by step. 

Output:

""",
    'keyword': """Input: Alexandra boarded the first flight of her grand journey, starting from Canada. With a globe-trotting itinerary in hand, she was filled with excitement. Her first stop was Mexico, where she marveled at the Mayan ruins. From there, she explored the rainforests of Brazil and danced the tango in Argentina. 

Let's think step by step. 

Output: 
1. Analyze sentence: Alexandra boarded the first flight of her grand journey, starting from Canada.
This Sentence has country names: Canada
2. Analyze sentence: With a globe-trotting itinerary in hand, she was filled with excitement. 
This Sentence has country names: 
3. Analyze sentence: Her first stop was Mexico, where she marveled at the Mayan ruins. 
This Sentence has country names: Mexico
4. Analyze sentence: From there, she explored the rainforests of Brazil and danced the tango in Argentina.
This Sentence has country names: Brazil, Argentina
5.Combine results:
Canada, Mexico, Brazil, Argentina

Final Answer: [Canada, Mexico, Brazil, Argentina]

Input: The adventure led him to the peaks of Peru where he trekked to see the mysteries of Machu Picchu. He then headed to Chile to gaze at the vastness of the Atacama Desert. A quick detour to Uruguay and Paraguay allowed him to experience the vibrancy of the local cultures before returning back to Canada through Peru, Brazil and Mexico. 

Let's think step by step. 

Output: 
1. Analyze sentence: The adventure led him to the peaks of Peru where he trekked to see the mysteries of Machu Picchu. 
This Sentence has country names: Peru
2. Analyze sentence: He then headed to Chile to gaze at the vastness of the Atacama Desert. 
This Sentence has country names: Chile
3. Analyze sentence: A quick detour to Uruguay and Paraguay allowed him to experience the vibrancy of the local cultures before returning back to Canada through Peru, Brazil and Mexico. 
This Sentence has country names: Uruguay, Paraguay, Canada, Peru, Brazil, Mexico
4.Combine results:
Peru, Chile, Uruguay, Paraguay, Canada, Peru, Brazil, Mexico

Final Answer: [Peru, Chile, Uruguay, Paraguay, Canada, Peru, Brazil, Mexico]

Input: Journeying westward, she admired the art in Italy and sipped coffee in France. The music of Spain and the history of Greece deepened her love for Europe. The Nordic beauty of Norway, Sweden, Finland, and Denmark took her breath away. She danced in Ireland, explored castles in Scotland, and marveled at the architecture in Germany and Russia. Italy, Norway, Sweden and Germany will always stay her favourite destinations to visit.

Let's think step by step. 

Output: 

1. Analyze sentence: Journeying westward, she admired the art in Italy and sipped coffee in France. This Sentence has country names: Italy, France
2. Analyze sentence: The music of Spain and the history of Greece deepened her love for Europe. 
This Sentence has country names: Spain, Greece
3. Analyze sentence: The Nordic beauty of Norway, Sweden, Finland, and Denmark took her breath away.
This Sentence has country names:  Norway, Sweden, Finland, Denmark 
4. Analyze sentence: She danced in Ireland, explored castles in Scotland, and marveled at the architecture in Germany and Russia. 
Ireland, Scotland, Germany, Russia
5. Analyze sentence: Italy, Norway, Sweden, Germany
6.Combine results:
Italy, France, Spain, Greece, Norway, Sweden, Finland, Denmark, Ireland, Scotland, Germany, Russia, Italy, Norway, Sweden, Germany

Final Answer: [Italy, France, Spain, Greece, Norway, Sweden, Finland, Denmark, Ireland, Scotland, Germany, Russia, Italy, Norway, Sweden, Germany]

Input: {query}

Let's think step by step. 

Output:
""",
    'healthcare': """Input: A 71-year-old male with COPD and diabetes presents with fever (101.2°F) for 3 days, dry cough for 3 days, and fatigue for 4 days. O2 saturation is 96%.

Let's think step by step

Output:
Symptoms: fever (3), dry cough (3), fatigue (4)
Vitals: O2 sat 96%, Temp 101.2°F
Check red flag symptoms → chest pain ❌, shortness of breath ❌, confusion ❌
→ red\_flag = false
Check viral cluster: fever ✅, cough ✅, fatigue ✅
→ viral\_cluster = likely
All symptoms ≥ 3 days → duration = 3+
→ Recommend: outpatient evaluation

Final answer: Outpatient evaluation

---

Input: A 45-year-old woman presents with fever (102°F), dry cough, and fatigue, all starting this morning. No known comorbidities. O2 saturation 98%.

Let's think step by step

Output:
Symptoms: fever (0), dry cough (0), fatigue (0)
Vitals: O2 sat 98%, Temp 102°F
Check red flag symptoms → chest pain ❌, shortness of breath ❌, confusion ❌
→ red\_flag = false
Check viral cluster: fever ✅, cough ✅, fatigue ✅
→ viral\_cluster = likely
All symptoms < 3 days → duration = 0
→ Recommend: home care

Final answer: Home care

---

Input: A 67-year-old male presents with chest pain and shortness of breath. History of hypertension. O2 saturation 92%.

Let's think step by step

Output:
Symptoms: chest pain ✅, shortness of breath ✅
Vitals: O2 sat 92%
Check red flag symptoms → chest pain ✅, shortness of breath ✅
→ red\_flag = true
→ Recommend: ER referral

Final answer: ER referral

Input: {query}

Let's think step by step. 

Output:
"""
    


}


class ZeroCoT(BaseScheme):
    
    def prep_const_prompt(self):
        self.cot_prompt = "Let's think step by step"

    def prep_task_spcefics(self):
        self.context = ContextPrompts[self.args.task]

    def extract_answer(self, output):
        # print(output)
        if self.args.task == 'keyword':
            final_output = self.llm_answer(f"format the answer {output} in a one-line list (square brackets) without quotes. example: [Country, Country, Country, ..., Country]")
        elif self.args.task == 'yelp':
            final_output = self.llm_answer(f"Based on the {output}, output the number of positive reviews. Output only an integer.")
        elif self.args.task == 'healthcare':
            final_output = self.llm_answer(f"Based on the {output}, output the final answer for the correct treatment.")
        else:
            final_output = self.llm_answer("extract the numerical of the answer:"+output)


        logging.info(f'>>>>>>>>>>>> final result: {output} vs ground truth: {self.ground_truth} <<<<<<<<<<<<<')
        input('finished 1 sample===> pause|')
        return final_output

    def solve_query(self, query):
        print(query)
        output = self.llm_answer(self.context + query + self.cot_prompt)
        print()
        print()
        print(output)
        print()
        print()
        output = self.extract_answer(output)
        return output

class ChainofThought(ZeroCoT):
    
    def prep_task_spcefics(self):
        self.context = ContextPrompts[self.args.task]
        self.cot_example = Task_Specific_Example.get(self.args.task)

    def solve_query_once(self, query):
        print(query)
        output = self.llm_answer(self.context + self.cot_example.format(query=query))
        print()
        print()
        print(output)
        print()
        print()
        output = self.extract_answer(output)

        # logging.info(f'>>>>>>>>>>>> final result: {output} <<<<<<<<<<<<<')
        # print(self.ground_truth)
        # input()
        return output

    def solve_query(self, query):
        return self.solve_query_once(query)

class SelfConsistentCoT(ChainofThought):

    def solve_query(self, query):
        output_list = []
        for __ in range(5):
            output = self.solve_query_once(query)
            output_list.append(output)

        counter = Counter(output_list)
        most_common_count = counter.most_common(1)[0][1]

        # Find all candidates with the most common count
        candidates = [key for key, count in counter.items() if count == most_common_count]

        # Randomly select one if tied
        return random.choice(candidates)