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
    current_num = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('##') or not line:
            continue
            
        # 解析动作编号和名称
        if line[0].isdigit() and '. ' in line:
            num_str, action = line.split('. ', 1)
            try:
                current_num = int(num_str)
                actions[current_num] = {
                    "action": action.strip(),
                    "preconditions": []
                }
            except ValueError:
                current_num = None
                
        # 解析前置条件
        elif line.startswith('-') and current_num is not None:
            precondition = line[1:].strip()
            actions[current_num]["preconditions"].append(precondition)
            
    return actions

# 生成并保存动作字典
action_dict = parse_actionbase(ACTIONBASE)
with open('../config/action_base.json', 'w') as f:
    json.dump(action_dict, f, indent=4, ensure_ascii=False)