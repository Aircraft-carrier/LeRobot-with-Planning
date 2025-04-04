import json

ACTIONBASE = """
## Action Base:
1. Grab strawberries from the table
- Gripper is empty.
- Strawberries are visible and reachable on the table.
2. Put the strawberries in the refrigerator
- Gripper is holding strawberries securely.
- Refrigerator door is fully open (achieved by Action 3).
3. Open the refrigerator door
- Refrigerator door is initially closed.
4. closed the refrigerator
- Refrigerator door is initially open.
"""  

def parse_actionbase(actionbase_str):
    actions = {}
    lines = actionbase_str.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('##') or not line:
            continue
        if '. ' in line:
            num_str, action = line.split('. ', 1)
            try:
                num = int(num_str)
                actions[num] = action.strip()
            except ValueError:
                continue
    return actions

# 生成并保存动作字典
action_dict = parse_actionbase(ACTIONBASE)
with open('../config/actions.json', 'w') as f:
    json.dump(action_dict, f, indent=4)