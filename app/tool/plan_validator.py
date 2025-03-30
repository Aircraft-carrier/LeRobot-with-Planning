from typing import Dict, List, Literal, Optional
from pydantic import Field
from app.exceptions import ToolError
from app.tool.base import BaseTool, ToolResult
from app.schema import Message
from app.llm import LLM
import json

class PlanValidator(BaseTool):
    """Validates generated plans against task requirements"""
    
    name: str = "validate_plan"
    description: str = "Determine whether the generated action plan sequence can successfully complete the task"
    parameters: dict = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Plan validation status. Available statuses: plan_generated_successfully, plan_generation_failed",
                "enum" :[
                    "plan_generated_successfully",
                    "plan_generation_failed"
                ]
            }
        },
        "required": ["status"],
        "additionalProperties": False
    }
    llm: LLM = Field(default_factory=lambda: LLM())

    async def execute(self,task: str, plans: str) -> ToolResult:     
        user_msg = f"""## Task\n{task}## Action plan sequence\n{plans}"""
        user_msg = Message.user_message(user_msg)
        system_msg = Message.system_message("You are an agent skilled in making independent judgments based on input requirements.")
        response = await self.llm.ask_tool(
            messages=[user_msg],
            system_msgs=[system_msg],
            tools=[self.to_param()],
            tool_choice="auto"
        )
        if response.tool_calls:
            for tool_call in response.tool_calls:
                # Parse the arguments
                args = tool_call.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        print(f"Failed to parse tool arguments: {args}")
                        continue
        if tool_call.function.name == "validate_plan":
            status = args.get("status")
        return ToolResult(
            output = (status ==  "plan_generated_successfully")
        )

