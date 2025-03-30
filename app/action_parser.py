import json

ACTIONBASE = """
## Action Base:
1. Grasp a Lego block and put it in the bin.
2. Open the fridge door.
3. Pick up the mop and lean it against the wall.
4. Grab a cup from the table and place it in the sink.
5. Close the cupboard door after retrieving an item.
6. Pick up the remote control and place it on the coffee table.
7. Grasp the towel and hang it on the rack.
8. Open the drawer and take out a spoon.
9. Pick up the book from the shelf and set it on the desk.
10. Grasp the trash bag and throw it into the bin.
11. Open the microwave door and remove the food container.
12. Pick up a pen and place it in the pencil holder.
13. Grasp the notebook and close it before putting it on the shelf.
14. Open the window and adjust the curtains.
15. Pick up the keys from the table and put them in the drawer.
16. Grasp a bottle of water from the fridge and place it on the counter.
17. Open the dishwasher and remove the clean dishes.
18. Pick up the cleaning spray and place it under the sink.
19. Grasp the smartphone from the couch and put it on the charging dock.
20. Open the closet door and hang up the jacket.
21. Grab strawberries from the table
22. Put the strawberries in the refrigerator
23. Open the refrigerator door
24. Turn off the refrigerator
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