from openai import OpenAI
import UserAgentPrompts as user_prmpt
import re
class OAI:
    def __init__(self,oai_key) -> None:
        self._client = OpenAI(
        api_key=oai_key,
        )
    def generate_prompt(self, prompt):
    # print(f"the prompt:{prompt}\n\n----")
        response = self._client.chat.completions.create(
            model="gpt-3.5-turbo-0613",  # or any other engine you prefer
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        generated_text = response.choices[0].message.content
        print(generated_text)
        return generated_text


class UserAgent():
    def __init__(self,goals,oai_key,dial_key) -> None:
        self.goals = [self.remove_span_tags(goal) for goal in goals]
        self.dial_key = dial_key
        print(f"Goals: {self.goals}")
        print(f"Key: {self.dial_key}")
        self.goal_cursor = 0
        self.model = OAI(oai_key=oai_key)
        self.history = ""
    def changeGoals(self,new_goals):
        self.goals = new_goals
        self.goal_cursor = 0
    def change_goal_cursor(self,goal_index):
        self.goal_cursor = goal_index
    def addDialogue(self, dialog):
        self.history += dialog
    def resetHistory(self):
        self.history = ""
    def generate_utterance(self):
        print("*"*15+"User"+"*"*15)
        result = "Satisfied"
        while self.history and result.startswith("Satisfied") and self.goal_cursor<len(self.goals):
            ## goal_window initially 2
            subgoals = self.goals[self.goal_cursor]
            if(self.goal_cursor<len(self.goals)-1):
                subgoals += " " +self.goals[self.goal_cursor+1]
            result = self.model.generate_prompt(
                user_prmpt.prompt_subgoalfinder(subgoals,self.history))
            print(f"result.startswith('Satisfied')={result.startswith('Satisfied')} goal={subgoals}")
            # if self.goal_cursor+1<len(self.goals) and self.goals[self.goal_cursor+1].startswith("If"): ## additional rules if the following rule is conditional
            #     if result.startswith("Satisfied"):
            #         self.goal_cursor +=2 #skip the if statement
            #     else:
            #         result = "Satisfied" # go into the the conditional goal
            #         self.goal_cursor +=1
            if result.startswith("Satisfied"):
                self.goal_cursor +=1
        print(self.history)
        print(f"Unsatisfied subgoal is: {result}")
        print("user response:")
        if self.goal_cursor == len(self.goals):
            print("Thanks")
            return "Thanks"
        else:
            user_request = self.model.generate_prompt(
                user_prmpt.prompt_requestgenerator(self.goals[self.goal_cursor],self.history,result))
            return user_request
    
    def remove_span_tags(self,text):
        # Regex pattern to match <span> tags and their contents
        pattern = r'<span.*?>(.*?)</span>'
        # Replace <span> tags with their contents
        return re.sub(pattern, r'\1', text)

