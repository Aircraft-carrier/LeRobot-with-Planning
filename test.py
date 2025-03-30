from app.tool.action_planning import ActionPlanningTool
from app.llm import LLM
from app.schema import Message
import asyncio  
import nest_asyncio
nest_asyncio.apply()

user_msg = Message.user_message("Help me put the strawberries in the fridge")
system_msg = Message.system_message("You are an agent who can control a robotic arm and perform a series of actions using the arm")

llm = LLM()
planning_tool = ActionPlanningTool()

async def make_request():
    response = await llm.ask_tool(
        messages=[user_msg],
        system_msgs=[system_msg],
        tools=[planning_tool.to_param()],
        tool_choice="auto"
    )
    return response

response = asyncio.run(make_request())
result = planning_tool.execute(command="get", plan_id="plan_001")
print(result.output)
