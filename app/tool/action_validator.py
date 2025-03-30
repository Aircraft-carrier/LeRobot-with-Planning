from pydantic import Field
from app.exceptions import ToolError
from app.tool.base import BaseTool, ToolResult
from app.schema import Message
from app.llm import LLM
import json
import base64
import os
from mimetypes import guess_type

class ActionValidator(BaseTool):
    """Validates robotic arm actions and provides replan feedback"""
    
    name: str = "validate_robotic_action"
    description: str = "Determine robotic arm action status and provide feedback"
    parameters: dict = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Validation status. Options: action_execute_successfully, action_execute_failed",
                "enum": [
                    "action_execute_successfully",
                    "action_execute_failed",
                ]
            },
            "feedback": {
                "type": "string",
                "description": "Required when unplanned event occurred. (e.g. 'An apple fell out when opening refrigerator')"
            }
        },
        "required": ["status"],
        "additionalProperties": False
    }
    llm: LLM = Field(default_factory=lambda: LLM())

    async def execute(self, action: str, initial_state_path: str, post_action_path: str) -> ToolResult:
        def load_image_as_base64(image_path: str) -> tuple:
            if not os.path.exists(image_path):
                raise ToolError(f"Image file not found: {image_path}")
            
            mime_type, _ = guess_type(image_path)
            if mime_type not in ["image/png", "image/jpeg"]:
                raise ToolError(f"Unsupported image format: {mime_type}")
            
            with open(image_path, "rb") as image_file:
                return (
                    base64.b64encode(image_file.read()).decode("utf-8"),
                    mime_type or "image/jpeg"
                )
        try:
            init_b64, init_mime = load_image_as_base64(initial_state_path)
            post_b64, post_mime = load_image_as_base64(post_action_path)
        except ToolError as e:
            return ToolResult(output=False, error=str(e))

        user_msg_text = f"""Analyze robotic arm operation:
        
        Command: {action}

        Compare initial (1st image) and post-action (2nd image) states.

        Judgment Criteria:

        [SUCCESS] Successfully completed the specified task
        [FAILURE] If:
        - The task is incomplete.
        - The environment remains largely unchanged.
        - Allowing the original action to be executed again.
        """

        user_msg = [
            {"type": "text", "text": user_msg_text},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{init_mime};base64,{init_b64}",
                    "detail": "high"
                }
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{post_mime};base64,{post_b64}",
                    "detail": "high"
                }
            }
        ]

        user_msg = Message.user_message(user_msg)
        system_msg = Message.system_message(
            "You're a robotic operation analyst skilled in making independent judgments based on input requirements."
        )

        try:
            response = await self.llm.ask_tool(
                messages=[user_msg],
                system_msgs=[system_msg],
                tools=[self.to_param()],
                tool_choice="auto"
            )
        except Exception as e:
            raise ToolError(f"LLM API error: {str(e)}")

        status = "action_execute_failed"
        feedback = ""
        if response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call.function.name == self.name:
                    try:
                        args = json.loads(tool_call.function.arguments)
                        status = args.get("status", "action_execute_failed")
                        feedback = args.get("feedback", "")
                        break
                    except (json.JSONDecodeError, KeyError):
                        continue

        return ToolResult(
            output=(status == "action_execute_successfully"),
            metadata={
                "operation_status": status,
                "feedback": feedback,
                "command_executed": action,
                "visual_data": {
                    "initial_state": initial_state_path,
                    "post_action": post_action_path
                }
            }
        )