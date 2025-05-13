# yelp.py

import os
import logging
import datetime
import json
import csv
import ast
from typing import Dict, List, Callable, Union
from functools import partial
from ...graph_of_thoughts import controller, language_models, operations, prompter, parser

def score_review_classification(state: Dict) -> float:
    """
    Function to score the LLM's classification of reviews.
    Lower scores are better (representing fewer errors).
    
    :param state: Thought state to be scored.
    :type state: Dict
    :return: Number of errors (lower is better).
    :rtype: float
    """
    try:
        current_count = int(state["current"])
        ground_truth = int(state["ground_truth"])
        return abs(current_count - ground_truth)
    except:
        return 100  # High error score for invalid responses

def test_review_classification(state: Dict) -> bool:
    """
    Function to test whether the final solution matches ground truth.
    
    :param state: Thought state that represents the final solution.
    :type state: Dict
    :return: Returns whether the solution matches the ground truth.
    :rtype: bool
    """
    try:
        current_count = int(state["current"])
        ground_truth = int(state["ground_truth"])
        return current_count == ground_truth
    except:
        return False

class Prompter(prompter.Prompter):
    """
    Prompter provides the generation of prompts specific to the
    Yelp review classification for the language models.
    
    Inherits from the Prompter class and implements its abstract methods.
    """
    
    # Basic prompt for IO approach
    classify_prompt = """<Instruction> Analyze the following list of Yelp reviews and determine how many of them express a positive sentiment overall. Each item in the list represents a complete customer review which may contain multiple sentences and complex opinions. A positive review generally expresses overall satisfaction with the business despite possibly mentioning minor issues, while a negative review expresses significant dissatisfaction even if some positive aspects are mentioned. After analyzing each review, output only the total number of positive reviews, with no additional explanation or text. </Instruction>

<Examples>
Input:
["I've given up trying to like this place. If you're a female, the servers ignore you. The food is subpar. The Reuben was served without thousand island dressing and when I asked for a side of it, the server told me there was already dressing on the sandwich-and never got me a side. The grilled cheese was a complete joke-2 pieces of white bread with 1 slice of American cheese, barely toasted! I could do better than that in my sleep. The tomato soup was the worst I've ever tasted. The fried pickles tasted delicious but clearly were made with minimal effort since only half actually had batter on them. The only redeeming part of this meal was the potato bacon soup. Your money is better spent elsewhere."]
Output: 0

Input:
["For starters the food sucks and the staff at night are very rude. If you don't know what you want right away they skip over you and have no patience. Glass is broken all the time. People get into fights. The bouncers who kick people out dragged an African American man out by his hood across the floor. They kick people out for just not liking them. They go over maximum capacity all the time. The bar deserves to be shutdown.", "Wow. What a fantastic experience. From the drinks to the food to the bartender to the company we couldn't ask for more. We couldn't have asked for anything better for the first bar we've tried in west Chester", "Everything we ate was great and the decor is fantastic. \nHighly recommend the BFD wings & the pork belly appetizer! \nGrab a Guinness!"]
Output: 2

Input:
["Holy greasy spoon Batman. They have taken their grease to whole new levels - coating the floor, chairs and windows with the stuff. The place is just downright N.A.S.T.Y. And I have had my share of Jersey diner experiences, but at least they were fast, descent and a reasonable value. This place is an overpriced pit where they stack you up and had you your check with your food just to let you know that you should, in fact, flee as quickly as you can. For those looking for 'a Nashville original' jump in your car and head to the Loveless Cafe or Pancake Pantry 'cuz this place is gross, loud, and you need to runaway!", "I love the soda shop! Been coming here for years . \nThe food is always on point. Love the new place.", "This is the best place in Nashville for a milkshake! I have not had the food so can only review the shake. Awesome.", "Third time at this establishment. I really want to ""like"" this small place, but The service is just so amazingly bad..... cool concept/history is the only thing going. Three strikes. XXX. We are out. Peace!"]
Output: 2
</Examples>

Input:
{input}
"""

    # Prompt for Chain-of-Thought approach
    classify_prompt_cot = """<Instruction> Analyze the following list of Yelp reviews and determine how many of them express a positive sentiment overall. Each item in the list represents a complete customer review which may contain multiple sentences and complex opinions. For each review, explain your reasoning about whether it's positive or negative, and then provide the final count of positive reviews, prefixed with "Output: ". </Instruction>

<Approach>
To classify complex Yelp reviews that may contain both positive and negative elements, follow these steps:
1. Read each review carefully, noting the overall tone and sentiment.
2. Identify key positive indicators: praise for food, service, or atmosphere; recommendations; expressions of enjoyment; intention to return.
3. Identify key negative indicators: complaints; criticism of important aspects like food, service, or cleanliness; expressions of disappointment; statements about not returning.
4. For mixed reviews, determine which sentiment dominates - does the reviewer seem more satisfied than dissatisfied overall?
5. Count the total number of reviews classified as positive.
</Approach>

<Examples>
Input:
["We no longer have to drive all the way to Deptford for good BBQ, Mullica Hill has needed a place like this for a long, long time! \n\nThey had some wait time issues when they first opened but have gotten things running smoothly since then. Every time I go there is better than the last. The sandwiches are oversize and you'll probably take half of it home for later.\n\nIt's clean, friendly and most of all, the food is great. \n\nP.S. do yourself a favor and park in the lower lot.", "Just an FYI to anyone concerned about getting sick- neither of the people cooking in the back had masks on. I arrived on time to pickup my food and had to stand and wait for 20 min because it wasn't ready and in addition to them I saw at least 2 other people without masks and those who were wearing them -were wearing them improperly."]

Review 1: "We no longer have to drive all the way to Deptford for good BBQ, Mullica Hill has needed a place like this for a long, long time! \n\nThey had some wait time issues when they first opened but have gotten things running smoothly since then. Every time I go there is better than the last. The sandwiches are oversize and you'll probably take half of it home for later.\n\nIt's clean, friendly and most of all, the food is great. \n\nP.S. do yourself a favor and park in the lower lot."
This review is clearly positive. The reviewer praises the food quality ("good BBQ", "food is great"), portion sizes ("oversize"), cleanliness ("It's clean"), and service ("friendly"). While they mention "wait time issues" in the past, they explicitly state these have been resolved ("gotten things running smoothly since then"). The enthusiasm is evident in phrases like "needed a place like this" and "Every time I go there is better than the last". This is a positive review.

Review 2: "Just an FYI to anyone concerned about getting sick- neither of the people cooking in the back had masks on. I arrived on time to pickup my food and had to stand and wait for 20 min because it wasn't ready and in addition to them I saw at least 2 other people without masks and those who were wearing them -were wearing them improperly."
This review is negative. It focuses entirely on health concerns (lack of masks during what appears to be the COVID-19 pandemic) and poor service (20-minute wait despite arriving on time). There are no positive aspects mentioned about the food or experience. The review is clearly meant as a warning to others. This is a negative review.

Total positive reviews: 1
Output: 1

Input:
["Maybe it's their Monday night crew or maybe this spot jumped the shark, but my experience last night was not the place I remember just a few years ago. It was staffed with all Gen Z'ers who felt really entitled for tips with the 3 or 4 tip jars you walked by while they struggled to simply scoop a small ice cream into a cone and make a crappy root beer float with a horrible ratio of soda to ice cream and charge you $15 for it. Never again. Don't believe the hype!", "Franklin Fountain has, without a doubt, the best ice cream and milkshakes I've ever eaten.\n\nMy favorite item on the menu (and I've tried a lot) is the Franklin Mint Shake, complete with homemade chocolate from Shane Confectionary (which has the same owners and is a couple doors down) as well as mint from Shane's rooftop, the result is a simultaneity decadent and refreshing milkshake. The texture of the shake is perfect, frothy and milky but not too thin. One of the best parts of the shake is when you reach the bottom, there's still lots of chocolate pieces to be enjoyed.\n\nOther shakes/ice cream flavors are also quite good. The coconut ice cream is chock-full of fresh coconut flakes, making for a powerful and delicious flavor. The Hydrox Cookie is full of chocolate and cream flavors, and also goes quite well in a shake.\n\nAs for sundaes, the Mount Vesuvius and the Franklin Mint are both delicious. The Mount Vesuvius is a brownie fudge sundae and is supremely rich and delicious. Brownies are freshly-baked an warm, as is the hot fudge. Vanilla and chocolate ice cream are the perfect bases for this delicious sundae. The Franklin Mint features vanilla bean ice cream, topped with hot fudge, crème de menthe sauce, and the same delicious chocolate in the mint shake. It is great also.\n\nIn the winter, given the chilly temperatures in Philly, Franklin Fountain unveils an innovative and delicious Winter menu. The S'mores hot milkshake on the winter menu is phenomenal. This shake features vanilla bean ice cream mixed with a warm, homemade graham cracker, homemade marshmallows flamed to toasty, and hot fudge. The end result is a beautiful product that tastes like warm melting ice cream. It is fantastic as all the flavors come together beautifully.\n\nFranklin may often have a wait, but it is completely worth waiting for every time for the outrageously good milkshakes and sundaes."]

Review 1: "Maybe it's their Monday night crew or maybe this spot jumped the shark, but my experience last night was not the place I remember just a few years ago. It was staffed with all Gen Z'ers who felt really entitled for tips with the 3 or 4 tip jars you walked by while they struggled to simply scoop a small ice cream into a cone and make a crappy root beer float with a horrible ratio of soda to ice cream and charge you $15 for it. Never again. Don't believe the hype!"
This review is clearly negative. The reviewer criticizes the service quality ("struggled to simply scoop"), product quality ("crappy root beer float", "horrible ratio"), value ("charge you $15 for it"), and staff attitude ("felt really entitled for tips"). Strong negative language is used throughout, and they explicitly state "Never again" and warn others "Don't believe the hype!" There are no positive elements mentioned. This is a negative review.

Review 2: "Franklin Fountain has, without a doubt, the best ice cream and milkshakes I've ever eaten.\n\nMy favorite item on the menu (and I've tried a lot) is the Franklin Mint Shake, complete with homemade chocolate from Shane Confectionary (which has the same owners and is a couple doors down) as well as mint from Shane's rooftop, the result is a simultaneity decadent and refreshing milkshake. The texture of the shake is perfect, frothy and milky but not too thin. One of the best parts of the shake is when you reach the bottom, there's still lots of chocolate pieces to be enjoyed.\n\nOther shakes/ice cream flavors are also quite good. The coconut ice cream is chock-full of fresh coconut flakes, making for a powerful and delicious flavor. The Hydrox Cookie is full of chocolate and cream flavors, and also goes quite well in a shake.\n\nAs for sundaes, the Mount Vesuvius and the Franklin Mint are both delicious. The Mount Vesuvius is a brownie fudge sundae and is supremely rich and delicious. Brownies are freshly-baked an warm, as is the hot fudge. Vanilla and chocolate ice cream are the perfect bases for this delicious sundae. The Franklin Mint features vanilla bean ice cream, topped with hot fudge, crème de menthe sauce, and the same delicious chocolate in the mint shake. It is great also.\n\nIn the winter, given the chilly temperatures in Philly, Franklin Fountain unveils an innovative and delicious Winter menu. The S'mores hot milkshake on the winter menu is phenomenal. This shake features vanilla bean ice cream mixed with a warm, homemade graham cracker, homemade marshmallows flamed to toasty, and hot fudge. The end result is a beautiful product that tastes like warm melting ice cream. It is fantastic as all the flavors come together beautifully.\n\nFranklin may often have a wait, but it is completely worth waiting for every time for the outrageously good milkshakes and sundaes."
This review is overwhelmingly positive. The reviewer uses superlative language throughout ("the best ice cream and milkshakes I've ever eaten", "perfect", "phenomenal", "outrageously good"). They provide extensive details about multiple menu items, all described in glowing terms. The only potential negative mentioned is that there "may often have a wait," but this is immediately followed by stating that it's "completely worth waiting for." The reviewer has clearly visited multiple times and tried numerous menu items. This is a positive review.

Total positive reviews: 1
Output: 1
</Examples>

Input:
{input}
"""
    
    # Prompt for Tree of Thoughts approach to improve a previous estimation
    tot_improve_prompt = """<Instruction> You previously analyzed a collection of Yelp reviews and determined that {previous_count} of them were positive. Please reanalyze these reviews more carefully, looking for subtle indicators of satisfaction or dissatisfaction that you might have missed. For mixed reviews, pay close attention to the overall tone and which aspects (positive or negative) the reviewer emphasizes more strongly. Consider the importance of different factors - a review that praises ambiance but criticizes food quality may be negative overall since food is typically the most important aspect of a restaurant experience. After your reanalysis, provide your revised count of positive reviews. </Instruction>

<Approach>
To improve your classification of complex Yelp reviews, follow these steps:
1. Reread each review carefully, noting both explicit statements and implicit tone.
2. For mixed reviews, determine which sentiment dominates by:
   - Assessing which aspects receive the most emphasis (length of discussion)
   - Identifying the reviewer's final impression or conclusion
   - Considering the importance of different factors (food quality usually outweighs décor)
   - Looking for "deal-breaker" complaints (e.g., poor hygiene, very bad service)
3. Watch for sarcasm or backhanded compliments that might seem positive at first glance.
4. Consider the review length - sometimes longer reviews with mostly criticism but a few token positive comments are still negative overall.
5. After thorough reanalysis, provide your revised count of positive reviews.
</Approach>

<Examples>
Input:
["Good, simple, classic Italian BYOB in Center City Philadelphia. Used to go to this place all the time back in the early 2000s and loved it. Menu hasn't changed and it really shouldn't.", "We have been going to this restaurant for 17 years. It is the most consistantly great place...ever. Don't pay attention to any 3 star reviews. You will get an amazingly tasty meal with amazing service. Yes, it is a small place, but it is intimate with friendly curteous service. You can order anything ""off the menu"". It's like having a personal chef making your dinner...or lunch. Favorites are the calamari, eggplant, lamb, chicken parm. Trust me...it's great.", "I advise anyone to stay away from this place, unless you enjoy being insulted/yelled at by the restaurant owners. \n\nService was rude from the minute we walked in. We were meeting friends who had been holding a table for us. Granted we were running a bit late, but there was NO ONE else waiting so we really didn't think it was necessary to treat us like criminals. \n\nThe restaurant is so crowded that one has hardly room to breathe. When the lady who would later serve us (presumably one of the restaurant owners) was standing by the door, my friend could not get up to go to the bathroom. I asked her politely if she could move to the side so my friend could go use the restroom, she told me in a very rude voice to ""just wait"" (not sure what she was doing...). \n\nWe were also told that we would have to vacate the table in 45 min (although it turned out no one had reserved our table)\n\nWe were later joined by two other friends who did not eat an entree (but four of us ordered appetizer, entree, dessert and coffee, spending over $30 per person), but at no point in the process did they have to make ANYONE wait on a table or turn anyone away because we were ""taking up"" their precious seats. I suppose this was still enough reason for them to categorize us as customers who came to take advantage of their restaurant. Our candle at the table was never lit, and every one of our dishes was served with a good dose of contempt. \n\nWhen the bill came, we were quite surprised to find corking charges and roughly 20% gratuity added to our bill (neither was mentioned anywhere on the menu or by our server). When we politely inquired about these charges, we were yelled at by the restaurant owner (presumably husband of afore-mentioned lady) that he had been in the restaurant business for over 20 years and that we were not in a position to tell him what to do. \n\nFood was decent but by far did not offset even a fraction of the terrible experience."]
Previous count: 1

Reanalysis:
Let me carefully reconsider each of these reviews:

Review 1: "Good, simple, classic Italian BYOB in Center City Philadelphia. Used to go to this place all the time back in the early 2000s and loved it. Menu hasn't changed and it really shouldn't."
On closer examination, this review is positive but with some potential nuance. The reviewer describes the restaurant as "good" (not great or excellent), mentions they "used to" go there frequently (past tense), and notes the menu hasn't changed which they frame positively ("it really shouldn't"). The overall sentiment is one of appreciation for consistency and simplicity. There are no complaints or criticisms. This is a positive review.

Review 2: "We have been going to this restaurant for 17 years. It is the most consistantly great place...ever. Don't pay attention to any 3 star reviews. You will get an amazingly tasty meal with amazing service. Yes, it is a small place, but it is intimate with friendly curteous service. You can order anything ""off the menu"". It's like having a personal chef making your dinner...or lunch. Favorites are the calamari, eggplant, lamb, chicken parm. Trust me...it's great."
This review is overwhelmingly positive with no criticisms. The reviewer has been a loyal customer for 17 years, uses superlatives ("most consistently great place...ever"), praises both the food and service, and specifically recommends menu items. They even defend the restaurant against moderate (3-star) reviews. This is clearly a positive review.

Review 3: "I advise anyone to stay away from this place, unless you enjoy being insulted/yelled at by the restaurant owners. \n\nService was rude from the minute we walked in. We were meeting friends who had been holding a table for us. Granted we were running a bit late, but there was NO ONE else waiting so we really didn't think it was necessary to treat us like criminals. [...]"
This long review details multiple instances of rude service, uncomfortable dining conditions, and questionable business practices. The reviewer explicitly advises others to "stay away" and states that even though the "food was decent," it "by far did not offset even a fraction of the terrible experience." The reviewer's strong negative feelings about the service completely overwhelm the mild positive comment about the food. This is a negative review.

After careful reanalysis, I find that 2 of the 3 reviews are positive.
Output: 2
</Examples>

Input:
{input}
Previous count: {previous_count}
"""

    # Prompt for GoT approach to split reviews into smaller chunks
    got_split_prompt = """<Instruction> Split the following list of Yelp reviews into 2 groups of approximately equal size. These reviews vary in length and complexity - some may be short while others contain multiple paragraphs of detailed experiences. Split them into two balanced groups without changing any of the content. Output only the final groups in the following format without any additional text or thoughts:
{{
    "Group 1": [review1, review2, ...],
    "Group 2": [review3, review4, ...]
}} </Instruction>

<Example>
Input:
["My mouth has never watered so much, while waiting for our order. We had the brisket sandwich (which is at least a pound of meat), pulled pork, fish and chips, potato salad and smoke clam chowder. The potato salad is a warm salad with fried potatoes, large chunks of bacon, green peppers, onions and mayo. There is a nice bright and country decorated dining area, but we took our food home with us.", "Wonderful destination for real deal BBQ! Brisket done right! Brisket and Beans and Truffle Fries fantastic can't miss sides! Milkshakes!!!!!", "We no longer have to drive all the way to Deptford for good BBQ, Mullica Hill has needed a place like this for a long, long time! \n\nThey had some wait time issues when they first opened but have gotten things running smoothly since then. Every time I go there is better than the last. The sandwiches are oversize and you'll probably take half of it home for later.\n\nIt's clean, friendly and most of all, the food is great. \n\nP.S. do yourself a favor and park in the lower lot.", "Just an FYI to anyone concerned about getting sick- neither of the people cooking in the back had masks on. I arrived on time to pickup my food and had to stand and wait for 20 min because it wasn't ready and in addition to them I saw at least 2 other people without masks and those who were wearing them -were wearing them improperly."]
Output: 
{{
    "Group 1": ["My mouth has never watered so much, while waiting for our order. We had the brisket sandwich (which is at least a pound of meat), pulled pork, fish and chips, potato salad and smoke clam chowder. The potato salad is a warm salad with fried potatoes, large chunks of bacon, green peppers, onions and mayo. There is a nice bright and country decorated dining area, but we took our food home with us.", "Wonderful destination for real deal BBQ! Brisket done right! Brisket and Beans and Truffle Fries fantastic can't miss sides! Milkshakes!!!!!"],
    "Group 2": ["We no longer have to drive all the way to Deptford for good BBQ, Mullica Hill has needed a place like this for a long, long time! \n\nThey had some wait time issues when they first opened but have gotten things running smoothly since then. Every time I go there is better than the last. The sandwiches are oversize and you'll probably take half of it home for later.\n\nIt's clean, friendly and most of all, the food is great. \n\nP.S. do yourself a favor and park in the lower lot.", "Just an FYI to anyone concerned about getting sick- neither of the people cooking in the back had masks on. I arrived on time to pickup my food and had to stand and wait for 20 min because it wasn't ready and in addition to them I saw at least 2 other people without masks and those who were wearing them -were wearing them improperly."]
}}
</Example>

Input:
{input}
"""

    # Prompt for GoT to merge multiple counts
    got_merge_prompt = """<Instruction> Combine the counts of positive reviews from two different groups to get the total number of positive reviews across all analyzed reviews. Group 1 has {count1} positive reviews and Group 2 has {count2} positive reviews. 
Only output the final combined count without any additional text or thoughts! </Instruction>

<Approach>
To determine the total count of positive reviews across all groups, add the count from Group 1 to the count from Group 2.
</Approach>

Group 1 positive reviews: {count1}
Group 2 positive reviews: {count2}

Combined total count:
"""

    def aggregation_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        """
        Generate an aggregation prompt for the language model.
        
        :param state_dicts: The thought states that should be aggregated.
        :type state_dicts: List[Dict]
        :param kwargs: Additional keyword arguments.
        :return: The aggregation prompt.
        :rtype: str
        """
        assert len(state_dicts) == 2, "Expected two states for aggregation prompt."
        
        return self.got_merge_prompt.format(
            count1=state_dicts[0]["current"],
            count2=state_dicts[1]["current"]
        )

    def generate_prompt(
        self, num_branches: int, original: str, current: str, method: str, **kwargs
    ) -> str:
        """
        Generate a generate prompt for the language model.
        
        :param num_branches: The number of responses the prompt should ask the LM to generate.
        :type num_branches: int
        :param original: Input reviews.
        :type original: str
        :param current: Intermediate solution.
        :type current: str
        :param method: Method for which the generate prompt is generated.
        :type method: str
        :param kwargs: Additional keyword arguments.
        :return: The generate prompt.
        :rtype: str
        """
        if current is None or current == "":
            input = original
        else:
            input = current
            
        if method.startswith("io"):
            return self.classify_prompt.format(input=input)
        elif method.startswith("cot"):
            return self.classify_prompt_cot.format(input=input)
        elif method.startswith("tot"):
            if current is None or current == "":
                return self.classify_prompt_cot.format(input=input)
            return self.tot_improve_prompt.format(
                input=original,
                previous_count=current
            )
        elif method.startswith("got"):
            if current is None or current == "":
                return self.got_split_prompt.format(input=input)
            
            if kwargs["phase"] == 1:
                return self.classify_prompt_cot.format(input=kwargs["sub_reviews"])
                
            # For improving a previous count in the GoT approach
            return self.tot_improve_prompt.format(
                input=original,
                previous_count=current
            )

    def improve_prompt(self, **kwargs) -> str:
        """
        Generate an improve prompt for the language model.
        
        :param kwargs: Additional keyword arguments.
        :return: The improve prompt.
        :rtype: str
        """
        pass

    def validation_prompt(self, **kwargs) -> str:
        """
        Generate a validation prompt for the language model.
        
        :param kwargs: Additional keyword arguments.
        :return: The validation prompt.
        :rtype: str
        """
        pass

    def score_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        """
        Generate a score prompt for the language model.
        
        :param state_dicts: The thought states that should be scored,
                            if more than one, they should be scored together.
        :type state_dicts: List[Dict]
        :param kwargs: Additional keyword arguments.
        :return: The score prompt.
        :rtype: str
        """
        pass

class Parser(parser.Parser):
    """
    Parser provides the parsing of language model responses
    specific to the Yelp review classification example.
    
    Inherits from the Parser class and implements its abstract methods.
    """
    
    def __init__(self) -> None:
        """
        Inits the response cache.
        """
        self.cache = {}
    
    def extract_count(self, text: str) -> str:
        """
        Helper function to extract the count of positive reviews from LLM response.
        
        :param text: The text to parse.
        :type text: str
        :return: The extracted count as a string.
        :rtype: str
        """
        # Try to find an "Output: N" pattern
        if "Output:" in text:
            output_parts = text.split("Output:")
            output_text = output_parts[-1].strip()
            # Extract just the number
            for word in output_text.split():
                if word.isdigit():
                    return word.strip()
        
        # If no output pattern, look for any standalone number
        for line in text.strip().split('\n'):
            line = line.strip()
            if line.isdigit():
                return line
        
        # If all else fails, try to extract any number from the text
        for word in text.split():
            if word.isdigit():
                return word
        
        # Default to 0 if no number found
        return "0"
        
    def parse_aggregation_answer(
        self, states: List[Dict], texts: List[str]
    ) -> Union[Dict, List[Dict]]:
        """
        Parse the response from the language model for an aggregation prompt.
        
        :param states: The thought states used to generate the prompt.
        :type states: List[Dict]
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The new thought states after parsing the responses from the language model.
        :rtype: Union[Dict, List[Dict]]
        """
        assert len(states) == 2, "Expected two states for aggregation answer."
        
        new_states = []
        for text in texts:
            count = self.extract_count(text)
            
            # Create a new state combining information from both input states
            new_state = states[0].copy()
            new_state["current"] = count
            if "sub_reviews" in states[0] and "sub_reviews" in states[1]:
                # Combine the sub_reviews if they exist
                new_state["sub_reviews"] = states[0]["sub_reviews"] + states[1]["sub_reviews"]
            new_states.append(new_state)
            
        return new_states

    def parse_generate_answer(self, state: Dict, texts: List[str]) -> List[Dict]:
        """
        Parse the response from the language model for a generate prompt.
        
        :param state: The thought state used to generate the prompt.
        :type state: Dict
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The new thought states after parsing the responses from the language model.
        :rtype: List[Dict]
        """
        new_states = []
        
        for text in texts:
            try:
                if state["method"].startswith("got") and state["current"] == "" and state["phase"] == 0:
                    # Parse the split reviews into groups
                    try:
                        # Extract the JSON structure
                        json_text = text[text.find("{"):text.rfind("}")+1]
                        groups = json.loads(json_text)
                        
                        # Create a state for each group
                        for key, reviews in groups.items():
                            new_state = state.copy()
                            new_state["current"] = ""
                            new_state["sub_reviews"] = str(reviews)
                            new_state["phase"] = 1
                            new_state["group"] = key
                            new_states.append(new_state)
                    except Exception as e:
                        logging.error(f"Error parsing split reviews: {e}")
                else:
                    # Parse the count of positive reviews
                    count = self.extract_count(text)
                    
                    new_state = state.copy()
                    new_state["current"] = count
                    new_state["phase"] = 2
                    new_states.append(new_state)
            except Exception as e:
                logging.error(f"Error parsing answer: {e}")
                
        return new_states

    def parse_improve_answer(self, state: Dict, texts: List[str]) -> Dict:
        """
        Parse the response from the language model for an improve prompt.
        
        :param state: The thought state used to generate the prompt.
        :type state: Dict
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The new thought state after parsing the responses from the language model.
        :rtype: Dict
        """
        pass

    def parse_validation_answer(self, state: Dict, texts: List[str]) -> bool:
        """
        Parse the response from the language model for a validation prompt.
        
        :param state: The thought state used to generate the prompt.
        :type state: Dict
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: Whether the thought state is valid or not.
        :rtype: bool
        """
        pass

    def parse_score_answer(self, states: List[Dict], texts: List[str]) -> List[float]:
        """
        Parse the response from the language model for a score prompt.
        
        :param states: The thought states used to generate the prompt.
        :type states: List[Dict]
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The scores for the thought states.
        :rtype: List[float]
        """
        pass

def io() -> operations.GraphOfOperations:
    """
    Generates the Graph of Operations for the IO method.
    
    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    operations_graph = operations.GraphOfOperations()
    
    operations_graph.append_operation(operations.Generate(1, 1))
    operations_graph.append_operation(operations.Score(1, False, score_review_classification))
    operations_graph.append_operation(operations.GroundTruth(test_review_classification))
    
    return operations_graph

def cot() -> operations.GraphOfOperations:
    """
    Generates the Graph of Operations for the Chain-of-Thought method.
    
    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    operations_graph = operations.GraphOfOperations()
    
    operations_graph.append_operation(operations.Generate(1, 1))
    operations_graph.append_operation(operations.Score(1, False, score_review_classification))
    operations_graph.append_operation(operations.GroundTruth(test_review_classification))
    
    return operations_graph

def tot() -> operations.GraphOfOperations:
    """
    Generates the Graph of Operations for the Tree of Thoughts method.
    
    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    operations_graph = operations.GraphOfOperations()
    
    operations_graph.append_operation(operations.Generate(1, 5))
    operations_graph.append_operation(operations.Score(1, False, score_review_classification))
    keep_best_1 = operations.KeepBestN(1, False)
    operations_graph.append_operation(keep_best_1)
    
    for _ in range(2):
        operations_graph.append_operation(operations.Generate(1, 5))
        operations_graph.append_operation(operations.Score(1, False, score_review_classification))
        keep_best_2 = operations.KeepBestN(1, False)
        keep_best_2.add_predecessor(keep_best_1)
        operations_graph.append_operation(keep_best_2)
        keep_best_1 = keep_best_2
    
    operations_graph.append_operation(operations.KeepBestN(1, False))
    operations_graph.append_operation(operations.GroundTruth(test_review_classification))
    
    return operations_graph

def got() -> operations.GraphOfOperations:
    """
    Generates the Graph of Operations for the Graph of Thoughts method.
    
    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    operations_graph = operations.GraphOfOperations()
    
    # Split the reviews into groups
    sub_groups = operations.Generate(1, 1)
    operations_graph.append_operation(sub_groups)
    
    # Process each group separately
    group_results = []
    for i in range(1, 3):  # Split into 2 groups
        group_id = f"Group {i}"
        group_selector = operations.Selector(
            lambda thoughts, id=group_id: [
                thought for thought in thoughts if thought.state.get("group") == id
            ]
        )
        group_selector.add_predecessor(sub_groups)
        operations_graph.add_operation(group_selector)
        
        # Generate classifications for this group - increased to 5 attempts
        classify_group = operations.Generate(1, 5)
        classify_group.add_predecessor(group_selector)
        operations_graph.add_operation(classify_group)
        
        # Score the classifications
        score_group = operations.Score(1, False, score_review_classification)
        score_group.add_predecessor(classify_group)
        operations_graph.add_operation(score_group)
        
        # Keep the best classification
        keep_best_group = operations.KeepBestN(1, False)
        keep_best_group.add_predecessor(score_group)
        operations_graph.add_operation(keep_best_group)
        
        group_results.append(keep_best_group)
    
    # Aggregate the results from all groups - increased to 5 attempts 
    final_aggregate = operations.Aggregate(5)
    for group_result in group_results:
        final_aggregate.add_predecessor(group_result)
    operations_graph.append_operation(final_aggregate)
    
    # Score and keep the best aggregation
    operations_graph.append_operation(operations.Score(1, False, score_review_classification))
    operations_graph.append_operation(operations.KeepBestN(1, False))
    
    # Verify against ground truth
    operations_graph.append_operation(operations.GroundTruth(test_review_classification))
    
    return operations_graph