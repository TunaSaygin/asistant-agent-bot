prompt_subgoalfinder = lambda goal,history: f"""
    From the given dialog history find out that the goal is satified or not.
    If you encounter [name], [address], [price] etc. , assume that these values are given.
    
    Wrong Example:
    Goal: You are looking for a place to stay. The hotel should have a star of 3 and should be in the south The hotel should be in the type of hotel and should include free parking
    History:
    User: Can you please provide me with a list of 3-star hotels located in the south? I am still looking for a place to stay.
    System: I found 2 hotels that match your request for 3-star hotels located in the south. The first one is the [bridge guest house], located at [151 hills road], with a phone number of [01223247942] and a postcode of [cb28rj]. The second one is [the lensfield hotel], located at [53-57 lensfield road], with a phone number of [01223355017] and a postcode of [cb21en]. Let me know if you need any further assistance or if you would like to book a hotel.
    Not satisfied. The system provided a list of 2 hotels that match the user's request for 3-star hotels located in the south.
    Reasoning: This is a wrong example because system is providing a list of 2 hotels is correct step for the goal's achievement. Explanation must give what should be done to achieve the goal.
    
    Correct Example:
    Goal: You are looking for a place to stay. The hotel should have a star of 3 and should be in the south The hotel should be in the type of hotel and should include free parking
    History:
    User: Can you please provide me with a list of 3-star hotels located in the south? I am still looking for a place to stay.
    System: I found 2 hotels that match your request for 3-star hotels located in the south. The first one is the [bridge guest house], located at [151 hills road], with a phone number of [01223247942] and a postcode of [cb28rj]. The second one is [the lensfield hotel], located at [53-57 lensfield road], with a phone number of [01223355017] and a postcode of [cb21en]. Let me know if you need any further assistance or if you would like to book a hotel.
    Not satisfied. The system provided list of 2 hotels that match user's request. User must chose a hotel among 2 hotels.
    Reasoning: This example is more accurate because it acknowledges that the user needs to choose one of the provided options and verify the inclusion of free parking to fully satisfy the goal.
    
    Correct Example:
    Goal:You want to book a taxi. The taxi should depart from saffron brasserie and should arrive by 03:30 The taxi should go to leicester train station
    History:
    User: Can you please book a taxi for me? I need to depart from Saffron Brasserie and arrive at my destination by 03:30.
    System: Sure, I can help you with that. May I know your destination, please?
    Not satisfied. Explanation: The user has mentioned the destination as "Leicester train station" which is not mentioned in the goal given as "The taxi should go to leicester train station."
    
    Wrong Example:
    Goal: You are looking for a restaurant. The restaurant should serve indian food and should be in the expensive price range Make sure you get area, address, and postcode
    History:
    User:Can you please recommend some Indian restaurants in Cambridge that are in the expensive price range?
    System: Assistant: Sure! Here are some Indian restaurants in Cambridge that are in the expensive price range:
    1. Curry Garden
    - Address: 106 Regent Street City Centre
    - Phone: 01223302330
    - Postcode: cb21dp
    2. The Golden Curry
    - Address: Mill Road City Centre
    - Phone: 01223329432
    - Postcode: cb12az
    Let me know if you need any further assistance!
    Satisfied. The system provided a list of Indian restaurants in Cambridge that are in the expensive price range, along with their area, address, and postcode.
    Reasoning: This is a bad example because the goal is unsatisfied. When the goal consist of instructions such as looking for or finding, user must ask for available options and then select one of the avaiable option to fulfill the goal 
    
    Response format:
    If satisfied Satsified. Explanation
    If not satisfied. Not. Expalanation
    
    Now find out whether the goal is satisfied or not.
    Goal:{goal}
    History:{history}
"""

prompt_requestgenerator = lambda goal,history,result: f"""
You are a user required to continue a conversation with an assistant bot given an unsatisfied goal and its explanation.
From the given dialogue history and unsatisfied goal with its reason, generate an appropriate user request that satisfies the goal and fits in the dialogue.
Focus on the reason for the unsatisfaction and on fulfilling the goal.
Focus on the unsatisfaction reason, and fulfilling the goal.

Wrong Example:
Goal: You are planning your trip in Cambridge. You are looking for a particular attraction. Its name is called cambridge and county folk museum
Reason of unsatisfaction: Dialogue hasn't started yet. 
History: 
Generated Utterance: Can you please recommend some popular tourist attractions in Cambridge?
Reasoning:  Rather than looking for a particular attraction called Cambridge and County Folk Museum, it asks for general tourist attractions.

Correct Example:
Goal: You are planning your trip in Cambridge. You are looking for a particular attraction. Its name is called cambridge and county folk museum
History: 
Generated Utterance: I am looking for an attraction.Can you provide information about the Cambridge and County Folk Museum in Cambridge?
Reasoning: Utterance clearly conveys the intent of user which is looking for a particular attraction. It covers all of the goal by giving information about cambridge and county folk museum

Wrong Example:
Goal: You are looking for a train. The train should leave on Thursday and should depart from Cambridge. The train should go to Peterborough and should leave after 20:15.
History: 
Generated Utterance: Can you please help me find a train that departs from Cambridge on Thursday?
Reasoning: The generated utterance does not fully satisfy the goal as it only mentions the departure location and day, but omits the destination (Peterborough) and the departure time (after 20:15).

Correct Example:
Goal: You are looking for a train. The train should leave on Thursday and should depart from Cambridge. The train should go to Peterborough and should leave after 20:15.
History: 
Generated Utterance: Can you please help me find a train that departs from Cambridge on Thursday after 20:15 and goes to Peterborough?
Reasoning: The generated utterance clearly includes all aspects of the goal, mentioning the departure location (Cambridge), the day (Thursday), the departure time (after 20:15), and the destination (Peterborough).

Now find the user's next utterance.
History:{history}
Goal:{goal}
Reason of unsatisfaction: {result}
        """