prompt_subgoalfinder = lambda goal,history: f"""
    From the given dialog history find out that the goal is satified or not.
    If you encounter [name], [address], [price] etc. , assume that these values are given.
    Response format:
    If satisfied Satsified. Explanation
    If not satisfied. Not. Expalanation
    Goal:{goal}
    History:{history}
"""

prompt_requestgenerator = lambda goal,history,result: f"""
            From the given dialogue history, and unsatisfied goal with its reason.
            Generate aproptriate user request that satify the goal and fits in the dialog
            History:{history}
            Goal:{goal}
            Reason of unsatisfaction: {result}
        """