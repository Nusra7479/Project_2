import psycopg2
import json
# from config import connection_string

# connection_string format: "db_name=<> user=<> password=<>" (no commas)

class Explain:
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string) # move this to inside fn? or to project.py


    def get_explain(self, query):

        cur = self.conn.cursor()
        cur.execute("EXPLAIN (FORMAT JSON) " + query)
        res = cur.fetchall()
        json_formatted_str = json.dumps(res, indent=2)
        print(json_formatted_str)
        return json_formatted_str

    def test(self):
        test_query_1 = "select * from public.customer limit 100"
        test_query_2 =  """select C.c_name, C.c_address, O.o_totalprice
                        from public.customer as C join public.orders as O on C.c_custkey = O.o_custkey
                        where C.c_acctbal < 5000
                        limit 100"""

        self.get_explain(test_query_1)



class QEPNode:
    def __init__(self, operation, children=None):
        self.operation = operation
        self.children = children if children is not None else []

    def add_child(self, child):
        self.children.append(child)

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


def generate_explanation(node1, node2):
    explanation = []

    if node1.operation != node2.operation:
        key = (node1.operation, node2.operation)
        explanation.append(explanation_mapping.get(key, f"The operation {node1.operation} has been changed to {node2.operation}."))

    common_children = min(len(node1.children), len(node2.children))

    for child1, child2 in zip(node1.children[:common_children], node2.children[:common_children]):
        explanation.extend(generate_explanation(child1, child2))

    # Handle additional or removed nodes in the select operation
    if len(node1.children) > len(node2.children):
        for child in node1.children[common_children:]:
            explanation.append(f"A {child.operation} node has been removed from the {node1.operation} operation.")
    elif len(node2.children) > len(node1.children):
        for child in node2.children[common_children:]:
            explanation.append(f"A new {child.operation} node has been added to the {node2.operation} operation.")

    return explanation



def explain_changes(qep_text1, qep_text2):
    tree1 = parse_qep(qep_text1)
    tree2 = parse_qep(qep_text2)

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
    json_plan = json.loads(json_qep)[0]["Plan"]
    return parse_qep_node(json_plan)


example_json_qep = '''
[
  {
    "Plan": {
      "Node Type": "Nested Loop",
      "Parallel Aware": false,
      "Join Type": "Inner",
      "Startup Cost": 0.0,
      "Total Cost": 7756209.0,
      "Plan Rows": 1500000,
      "Plan Width": 244,
      "Actual Startup Time": 8.015,
      "Actual Total Time": 11.419,
      "Actual Rows": 1500000,
      "Actual Loops": 1,
      "Plans": [
        {
          "Node Type": "Seq Scan",
          "Parent Relationship": "Outer",
          "Parallel Aware": false,
          "Relation Name": "customer",
          "Alias": "c",
          "Startup Cost": 0.0,
          "Total Cost": 3191.5,
          "Plan Rows": 1500,
          "Plan Width": 200,
          "Actual Startup Time": 0.008,
          "Actual Total Time": 0.631,
          "Actual Rows": 1500,
          "Actual Loops": 1
        },
        {
          "Node Type": "Seq Scan",
          "Parent Relationship": "Inner",
          "Parallel Aware": false,
          "Relation Name": "orders",
          "Alias":           "o",
          "Startup Cost": 0.0,
          "Total Cost": 5150677.0,
          "Plan Rows": 1500000,
          "Plan Width": 44,
          "Actual Startup Time": 0.006,
          "Actual Total Time": 4.133,
          "Actual Rows": 1500000,
          "Actual Loops": 1500
        }
      ]
    }
  }
]
'''

# Load the JSON QEP from the string
qep1 = parse_qep(example_json_qep)


example_json_qep2 = '''
[
  {
    "Plan": {
      "Node Type": "Nested Loop",
      "Parallel Aware": false,
      "Join Type": "Inner",
      "Startup Cost": 0.0,
      "Total Cost": 7756209.0,
      "Plan Rows": 1500000,
      "Plan Width": 244,
      "Actual Startup Time": 8.015,
      "Actual Total Time": 11.419,
      "Actual Rows": 1500000,
      "Actual Loops": 1,
      "Plans": [
        {
          "Node Type": "Index Scan",
          "Parent Relationship": "Outer",
          "Parallel Aware": false,
          "Relation Name": "customer",
          "Alias": "c",
          "Startup Cost": 0.0,
          "Total Cost": 3191.5,
          "Plan Rows": 1500,
          "Plan Width": 200,
          "Actual Startup Time": 0.008,
          "Actual Total Time": 0.631,
          "Actual Rows": 1500,
          "Actual Loops": 1
        },
        {
          "Node Type": "Seq Scan",
          "Parent Relationship": "Inner",
          "Parallel Aware": false,
          "Relation Name": "orders",
          "Alias": "o",
          "Startup Cost": 0.0,
          "Total Cost": 5150677.0,
          "Plan Rows": 1500000,
          "Plan Width": 44,
          "Actual Startup Time": 0.006,
          "Actual Total Time": 4.133,
          "Actual Rows": 1500000,
          "Actual Loops": 1500
        }
      ]
    }
  }
]
'''

# Parse the second example JSON QEP
qep2 = parse_qep(example_json_qep2)

# Generate explanations
explanations = generate_explanation(qep1, qep2)

# Print explanations
for explanation in explanations:
    print(explanation)
