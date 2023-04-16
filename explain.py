import psycopg2
import matplotlib.pyplot as plt

class Explain:
    # connection_string format: "db_name=<> user=<> password=<>" (no commas)
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)


    # returns plan JSON object
    def get_plan(self, query):
        cur = self.conn.cursor()
        try:
            cur.execute("EXPLAIN (FORMAT JSON) " + query)
        except Exception as e:
            self.conn.rollback()
            print(e)
            return None
        res = cur.fetchall()
        plan_object = res[0][0][0]
        return plan_object


    def test(self):
        test_query_1 = "select * from public.customer limit 100"
        test_query_2 =  """select C.c_name, C.c_address, O.o_totalprice
                        from public.customer as C join public.orders as O on C.c_custkey = O.o_custkey
                        where C.c_acctbal < 5000
                        limit 100"""

        self.get_plan(test_query_1)

class QEPNode:
    def __init__(self, operation, rows, relationName, children=None):
        self.operation = operation
        self.children = children if children is not None else []
        self.rows = rows
        self.relationName = relationName
        
    def add_child(self, child):
        self.children.append(child)

def visualize_tree(root, level=0, tree_print=''):
    if root is None:
        return tree_print

    # print('  ' * level + '+-' + str(root.operation))
    tree_print = tree_print + '  ' * level + '+-' + str(root.operation) + '\n'

    for child in root.children[:-1]:
        tree_print = visualize_tree(child, level + 1, tree_print)
        # print('  ' * (level + 1) + '|')
        tree_print = tree_print + '  ' * (level + 1) + '|' + '\n'

    if root.children:
        tree_print = visualize_tree(root.children[-1], level + 1, tree_print)

    return tree_print

def visualise_qep(qep, ax):
    tree = parse_qep(qep)
    vis = visualize_tree(tree)
    ax = visualize_tree_as_flowchart(tree, ax)
    ax.axis('off')
    print(vis)
    return vis, ax

def visualize_tree_as_flowchart(root, ax=None, x=0, y=0, x_offset=0, y_offset=0, level_height=1):
    if ax is None:
        fig, ax = plt.subplots()

    if root is None:
        return ax

    if 'scan' in root.operation.lower():
        # Draw the operation box
        ax.text(x + x_offset, y + y_offset, root.operation, ha='center', va='center',
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='round'))

        # Draw the relationship box
        ax.text(x + x_offset, y + y_offset - level_height, root.relationName, ha='center', va='center', #color='white',
                bbox=dict(facecolor='yellow', edgecolor='black', boxstyle='round'))

        # Draw a line connecting the operation and relationship boxes
        ax.plot([x + x_offset, x + x_offset], [y + y_offset, y + y_offset - level_height], 'k-')
    else:
        ax.text(x + x_offset, y + y_offset, root.operation, ha='center', va='center',
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='round',))

    # ax.text(x + x_offset, y + y_offset, root.operation, ha='center', va='center', bbox=dict(facecolor='white', edgecolor='black', boxstyle='round'))

    children = root.children
    if children:
        num_children = len(children)
        if num_children > 1:
            # Calculate the total width of children nodes
            children_width = num_children * level_height

            # Calculate the leftmost and rightmost x-coordinates for the children nodes
            leftmost_child_x = x - children_width // 2
            rightmost_child_x = x + children_width // 2

            # Update the x-coordinates for the child nodes based on the calculated leftmost and rightmost x-coordinates
            child_x_offsets = range(leftmost_child_x, rightmost_child_x + 1)
        else:
            # If there is only one child, place it directly below the parent node
            child_x_offsets = [x]
        # child_x_offsets = range(x - num_children // 2 + x_offset, x + num_children // 2 + 1 + x_offset)
        for child, child_x_offset in zip(children, child_x_offsets):
            ax = visualize_tree_as_flowchart(child, ax, child_x_offset, y - level_height, x_offset, y_offset, level_height)
            ax.plot([x + x_offset, child_x_offset], [y + y_offset, y - level_height + y_offset], 'k-')

    return ax

def compare_nodes(node1, node2):
    if node1.operation != node2.operation:
        return False

    if len(node1.children) != len(node2.children):
        return False
    
    # Same scan can be done on different tables: must return false
    if "Scan" in node1.operation:
        if node1.relationName != node2.relationName:
            return False


    for child1, child2 in zip(node1.children, node2.children):
        if not compare_nodes(child1, child2):
            return False

    return True


def compare_trees(tree1, tree2):
    return compare_nodes(tree1, tree2)


def min_edit_distance(node1_children, node2_children, memo=None):
    if memo is None:
        memo = {}

    if not node1_children:
        return len(node2_children)
    if not node2_children:
        return len(node1_children)

    if (len(node1_children), len(node2_children)) in memo:
        return memo[(len(node1_children), len(node2_children))]

    substitution = min_edit_distance(node1_children[1:], node2_children[1:], memo)
    if node1_children[0].operation != node2_children[0].operation:
        substitution += 1

    deletion = min_edit_distance(node1_children[1:], node2_children, memo) + 1
    insertion = min_edit_distance(node1_children, node2_children[1:], memo) + 1

    result = min(substitution, deletion, insertion)
    memo[(len(node1_children), len(node2_children))] = result
    return result

def generate_explanation(node1, node2):
    explanation = []

    # Same or different scans
    if "Scan" in node1.operation and "Scan" in node2.operation:
        # As long as different tables, generic explanation
        if node1.relationName != node2.relationName:
                explanation.append("The table '{relation2}' has been scanned instead of the table '{relation1}'.".format(relation2 = node2.relationName, relation1 = node1.relationName))

    else:
        if node1.operation != node2.operation:
            key = (node1.operation, node2.operation)
            mapping = explanation_mapping.get(key, f"The operation {node1.operation} has been changed to {node2.operation}.")
            if node1.operation in joins and node2.operation in joins:
                rows1 = node1.children[0].rows
                rows2 = node1.children[1].rows
                rows3 = node2.children[0].rows
                rows4 = node2.children[1].rows

                if rows3 > rows1 and rows4 > rows2:
                    explanation.append(mapping.format(n1c1 = rows1, n1c2 = rows2, n2c1 = rows3, n2c2 = rows4))
                if node1.operation == "Nested Loop" and node2.operation == "Hash Join":
                    explanation.append("A hash join is used because it is more efficient for the equi-join condition specified.")
                if node1.operation == "Nested Loop" and node2.operation == "Merge Join":
                    explanation.append("A merge join is used because one or both tables participating in the join can be sorted efficiently on the join key.")    
                if node1.operation == "Hash Join" and node2.operation == "Nested Loop":
                    explanation.append("A nested loop join is used because it is more efficient for the non-equi join condition specified.")        
                if node1.operation == "Hash Join" and node2.operation == "Merge Join":
                    explanation.append("A merge join is used because one or both tables participating in the join can be sorted efficiently on the join key.")    
                if node1.operation == "Merge Join" and node2.operation == "Nested Loop":
                    explanation.append("A nested loop join is used because it is more efficient for the non-equi join condition specified.")  
                if node1.operation == "Merge Join" and node2.operation == "Hash Join":
                    explanation.append("A hash join is used because it is more efficient for the equi-join condition specified.")     
            # Different scans
            elif "Scan" in node1.operation and "Scan" in node2.operation:
                # Must have Relation Name because scan
                # Must be same relation
                explanation.append(mapping)
            else:
                explanation.append(mapping)    
                

    edit_distance = min_edit_distance(node1.children, node2.children)
    matched_indices = []

    for i, child1 in enumerate(node1.children):
        min_dist = float('inf')
        min_j = -1

        for j, child2 in enumerate(node2.children):
            if j not in matched_indices:
                dist = min_edit_distance(child1.children, child2.children)
                if dist < min_dist:
                    min_dist = dist
                    min_j = j

        if min_j != -1:
            matched_indices.append(min_j)
            explanation.extend(generate_explanation(child1, node2.children[min_j]))

    for i, child1 in enumerate(node1.children):
        if i not in matched_indices:
            explanation.append(f"A {child1.operation} node has been removed from the {node1.operation} operation.")

    for j, child2 in enumerate(node2.children):
        if j not in matched_indices:
            explanation.append(f"A new {child2.operation} node has been added to the {node2.operation} operation.")

    return explanation


def explain_changes(qep1, qep2):
    tree1 = parse_qep(qep1)
    tree2 = parse_qep(qep2)

    if compare_trees(tree1, tree2):
        return "No changes detected between the two query execution plans."
    else:
        return "\n".join(generate_explanation(tree1, tree2))

joins = [
    'Hash Join',
    'Merge Join',
    'Nested Loop'
]

explanation_mapping = {
    ('Hash Join', 'Merge Join'): 'The number of rows in the first participating table has changed ' +
      'from {n1c1} to {n2c1} and the number of rows in the second participating table has changed from  {n1c2} to {n2c2}. ',
    ('Merge Join', 'Hash Join'): 'The number of rows in the first participating table has changed ' +
      'from {n1c1} to {n2c1} and the number of rows in the second participating table has changed from  {n1c2} to {n2c2}. ',
    ('Nested Loop', 'Hash Join'): 'The number of rows in the first participating table has changed ' +
      'from {n1c1} to {n2c1} and the number of rows in the second participating table has changed from  {n1c2} to {n2c2}. ',
    ('Hash Join', 'Nested Loop'): 'This is because the number of rows in the first participating table has changed ' +
      'from {n1c1} to {n2c1} and the number of rows in the second participating table has changed from  {n1c2} to {n2c2}. ',
    ('Nested Loop', 'Merge Join'): 'The number of rows in the first participating table has changed ' +
      'from {n1c1} to {n2c1} and the number of rows in the second participating table has changed from  {n1c2} to {n2c2}. ',
    ('Merge Join', 'Nested Loop'): 'The number of rows in the first participating table has changed ' +
      'from {n1c1} to {n2c1} and the number of rows in the second participating table has changed from  {n1c2} to {n2c2}. ',
    ('Seq Scan', 'Index Scan'): 'A sequential scan has been changed to an index scan, as an index was found to improve performance. ',
    ('Index Scan', 'Seq Scan'): 'An index scan has been changed to a sequential scan, as a sequential scan was determined to be more efficient in this case. ',
    ('Bitmap Index Scan', 'Index Scan'): 'A bitmap index scan has been changed to an index scan due to changes in the WHERE clause or the addition of an ORDER BY clause. ',
    ('Index Scan', 'Bitmap Index Scan'): 'An index scan has been changed to a bitmap index scan because it was determined to be more efficient for the query. ',
    ('Bitmap Heap Scan', 'Seq Scan'): 'A bitmap heap scan has been changed to a sequential scan because it was determined to be more efficient for the query. ',
    ('Seq Scan', 'Bitmap Heap Scan'): 'A sequential scan has been changed to a bitmap heap scan because it was determined to be more efficient for the query. ',
}


def parse_qep_node(json_node):
    operation = json_node["Node Type"]
    children = []
    rows = json_node["Plan Rows"]

    if "Relation Name" in json_node.keys():
        relationName = json_node["Relation Name"]
    else:
        relationName = None 

    if "Plans" in json_node:
        for child in json_node["Plans"]:
            children.append(parse_qep_node(child))

    return QEPNode(operation, rows, relationName, children)


def parse_qep(json_qep):
    root_object = json_qep["Plan"]
    return parse_qep_node(root_object)


# # testing for explain.py
# test_query_1 = "select * from public.customer "
# test_query_2 = "select * from public.customer limit 100"

# connection_string = "<connection_string>"
# conn = psycopg2.connect(connection_string)
# cur = conn.cursor()

# explain = Explain(connection_string)
# qep1 = explain.get_plan(test_query_1)
# qep2 = explain.get_plan(test_query_2)

# # Generate explanations
# explanations = explain_changes(qep1, qep2)

# # Print explanations
# print(explanations)