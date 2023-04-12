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