from interface import Analyzer_GUI
import PySimpleGUI as sg
from explain import Explain

gui = Analyzer_GUI()
win = gui.create_win()
explain = None

while True:
    event, values = win.read()
    if event == 'Connect to PostgreSQL Database':
        connection_string = gui.get_connection_string() # connection_string format: "db_name=<> user=<> password=<>" (no commas)
        explain = Explain(connection_string)
        print("conn", connection_string)

    if event == 'Test':
        samples = gui.get_sample_queries()
        samples_ind = int(values['samples'][-1])
        q_no = values['sam_q']
        if q_no == 'Query 1':
            q1 = samples[samples_ind]
            win['q1'].update(q1)

        elif q_no == 'Query 2':
            q2 = samples[samples_ind]
            win['q2'].update(q2)

    if event == 'Generate Explanation':
        q1 = values['q1']
        p1 = values['p1']
        q2 = values['q2']
        p2 = values['p2']


        ########################### Insert Explanation To Be Displayed Below ######################
        explanation = "Q1: " + q1 + "\nQ2: " + q2 + "\np1 " + p1 + "\np2 " + p2
        ############################################################################################

        win['res'].update(explanation)

    if event == 'Generate Query Plan':
        if not explain:
            sg.Popup("Please Connect to Database")
            continue

        q1 = values['q1']
        q2 = values['q2']

        print(q1)
        if q1:
            try:
                p1 = explain.get_explain(q1)
                win['p1'].update(p1)
            except:
                sg.Popup("Please check Query 1's format")

        if q2:
            try:
                p2 = explain.get_explain(q2)
                win['p2'].update(p2)
            except:
                sg.Popup("Please check Query 2's format")

    if event == 'Visualise Query Plan':
        p1 = values['p1']
        p2 = values['p2']

        gui.visualise_graph(p1)


    if event == sg.WIN_CLOSED:
        break

