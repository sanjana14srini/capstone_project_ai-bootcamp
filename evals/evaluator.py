import json
import os
from enum import Enum
from pydantic import BaseModel, Field
from pydantic_ai import Agent
import asyncio
from tqdm.auto import tqdm
import pandas as pd



class CheckName(str, Enum):
    instructions_follow = "instructions_follow"
    instructions_avoid = "instructions_avoid" 
    answer_relevant = "answer_relevant"
    answer_clear = "answer_clear"
    answer_citations = "answer_citations"
    completeness = "completeness"
    tool_call_search = "tool_call_search"

CHECK_DESCRIPTIONS = {
    CheckName.instructions_follow: "The agent followed the user's instructions (in <INSTRUCTIONS>)",
    CheckName.instructions_avoid: "The agent avoided doing things it was told not to do",
    CheckName.answer_relevant: "The response directly addresses the user's question",
    CheckName.answer_clear: "The answer is clear and correct",
    CheckName.answer_citations: "The response includes proper references or sources when required",
    CheckName.completeness: "The response is complete and covers all key aspects of the request",
    CheckName.tool_call_search: "Is the search tool invoked?"
}

class EvaluationCheck(BaseModel):
    check_name: CheckName = Field(description="The type of evaluation check")
    reasoning: str = Field(description="The reasoning behind the check result")
    check_pass: bool = Field(description="Whether the check passed (True) or failed (False)")
    
class EvaluationChecklist(BaseModel):
    checklist: list[EvaluationCheck] = Field(description="List of all evaluation checks")
    summary: str = Field(description="Evaluation summary")


def generate_checklist_text():
    checklist_items = []
    for check_name in CheckName:
        description = CHECK_DESCRIPTIONS[check_name]
        checklist_items.append(f"- {check_name.value}: {description}")
    return "\n".join(checklist_items)

evaluation_prompt = """
Use this checklist to evaluate the quality of an AI agent’s answer (<ANSWER>) to a user question (<QUESTION>).
We also include the entire log (<LOG>) for analysis.

For each item, check if the condition is met. 

Checklist:

- instructions_follow: The agent followed the user’s instructions (in <INSTRUCTIONS>)
- instructions_avoid: The agent avoided doing things it was told not to do  
- answer_relevant: The response directly addresses the user’s question  
- answer_clear: The answer is clear and correct  
- answer_citations: The response includes proper citations or sources when required  
- completeness: The response is complete and covers all key aspects of the request
- tool_call_search: Is the search tool invoked? 

Output true/false for each check and provide a short explanation for your judgment.
"""




eval_instructions = f"""
Use this checklist to evaluate the quality of an AI agent’s answer (<ANSWER>) to a user question (<QUESTION>).
We also include the entire log (<LOG>) for analysis.

For each item, check if the condition is met. 

Checklist:

{generate_checklist_text()}

Output true/false for each check and provide a short explanation for your judgment.
"""



eval_agent = Agent(
    name='eval_agent',
    model='gpt-5-mini',
    instructions=evaluation_prompt,
    output_type=EvaluationChecklist
)


user_prompt_format = """
<INSTRUCTIONS>{instructions}</INSTRUCTIONS>
<QUESTION>{question}</QUESTION>
<ANSWER>{answer}</ANSWER>
<LOG>{log}</LOG>
""".strip()

def format_prompt(file):

    question = file["messages"][0]["parts"][0]["content"]
    # reference = file["output"]["references"]

    answer = file["output"]["summary"]

    logs = file

    return user_prompt_format.format(
        instructions=eval_agent._instructions,
        question=question,
        answer=answer,
        log=logs
    )



async def main():
    all_results = []
    #TODO: specify correct directory location of logs
    directory_path = 'evals/latest_evals/eval_logs/'
    for file_name in os.listdir(directory_path):
        full_file_name = os.path.join('evals/latest_evals/eval_logs/', file_name)
        with open(full_file_name, 'r') as file:
            file_data = json.load(file)

        user_prompt = format_prompt(file_data)
        result = await eval_agent.run(user_prompt)

        all_results.append((file_data, result))

    
    eval_results = []

    for rec, result in all_results:
        eval_row = rec.copy()
        eval_result = result.output
        checks = {c.check_name.value: c.check_pass for c in eval_result.checklist}
        eval_row.update(checks)
        eval_row['summary'] = eval_result.summary
        eval_results.append(eval_row)


    df_eval = pd.DataFrame(eval_results)

    eval_columns = [check_name.value for check_name in CheckName]
      

    print("evaluations complete. now saving results.")
    all_metrics = pd.DataFrame({
    'metric': df_eval[eval_columns].mean().index,
    'score': df_eval[eval_columns].mean().values
        })
    all_metrics.to_csv("evals/latest_evals/all_metrics.csv")
    
    df_eval.to_csv("evals/latest_evals/evals.csv")
    




if __name__ == "__main__":
    asyncio.run(main())