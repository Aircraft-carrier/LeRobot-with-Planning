from app.tool.robot_action import RobotAction  
from app.tool.terminal import Terminal
import asyncio  


async def main():  
    args = {"action_id": 16}  
    tool = RobotAction()  
    result = await tool.execute(**args)  
    print("RobotAction : ",result)
    # terminal = Terminal()
    # result = await terminal.execute("python -u robot.py  --action='good'")


# Run the main function with asyncio  
if __name__ == "__main__":  
    asyncio.run(main())  