import psycopg2


class Explain:
    # connection_string format: "db_name=<> user=<> password=<>" (no commas)
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)


    # returns plan JSON object
    def get_plan(self, query):
        cur = self.conn.cursor()
        cur.execute("EXPLAIN (FORMAT JSON) " + query)
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
    def __init__(self, operation, children=None):
        self.operation = operation
        self.children = children if children is not None else []


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

def visualise_qep(qep):
    tree = parse_qep(qep)
    vis = visualize_tree(tree)
    print()
    print(vis)
    return vis

def compare_nodes(node1, node2):
    if node1.operation != node2.operation:
        return False

    if len(node1.children) != len(node2.children):
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

    if node1.operation != node2.operation:
        key = (node1.operation, node2.operation)
        explanation.append(explanation_mapping.get(key, f"The operation {node1.operation} has been changed to {node2.operation}."))

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


explanation_mapping = {
    ('hash_join', 'sort_merge_join'): 'A hash join has been changed to a sort-merge join due to changes in the WHERE clause.',
    ('sort_merge_join', 'hash_join'): 'A sort-merge join has been changed to a hash join due to changes in the WHERE clause.',
    ('nested_loop_join', 'hash_join'): 'A nested loop join has been changed to a hash join because a more efficient join strategy was determined.',
    ('hash_join', 'nested_loop_join'): 'A hash join has been changed to a nested loop join because a more efficient join strategy was determined.',
    ('nested_loop_join', 'sort_merge_join'): 'A nested loop join has been changed to a sort-merge join because a more efficient join strategy was determined.',
    ('sort_merge_join', 'nested_loop_join'): 'A sort-merge join has been changed to a nested loop join because a more efficient join strategy was determined.',
    ('seq_scan', 'index_scan'): 'A sequential scan has been changed to an index scan, as an index was found to improve performance.',
    ('index_scan', 'seq_scan'): 'An index scan has been changed to a sequential scan, as a sequential scan was determined to be more efficient in this case.',
    ('bitmap_index_scan', 'index_scan'): 'A bitmap index scan has been changed to an index scan due to changes in the WHERE clause or the addition of an ORDER BY clause.',
    ('index_scan', 'bitmap_index_scan'): 'An index scan has been changed to a bitmap index scan because it was determined to be more efficient for the query.',
    ('bitmap_heap_scan', 'seq_scan'): 'A bitmap heap scan has been changed to a sequential scan because it was determined to be more efficient for the query.',
    ('seq_scan', 'bitmap_heap_scan'): 'A sequential scan has been changed to a bitmap heap scan because it was determined to be more efficient for the query.',
    ('materialize', 'no_materialize'): 'Materialization has been removed due to changes in the query that made it unnecessary.',
    ('no_materialize', 'materialize'): 'Materialization has been added to improve the performance of a subquery or common table expression.',
}


def parse_qep_node(json_node):
    operation = json_node["Node Type"]
    children = []

    if "Plans" in json_node:
        for child in json_node["Plans"]:
            children.append(parse_qep_node(child))

    return QEPNode(operation, children)


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