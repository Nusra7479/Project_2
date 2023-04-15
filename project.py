from interface import Analyzer_GUI
import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from explain import Explain, explain_changes, visualise_qep
import json


gui = Analyzer_GUI()
win = gui.create_win()
explain = None
ax1 = None
ax2 = None
canvas1 = None
canvas2 = None

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
        win['exp_tab'].select()

        if not (p1 and p2):
            sg.Popup('Please input 2 query plans')
            continue
        ########################### Insert Explanation To Be Displayed Below ######################
        p1_json = json.loads(p1)
        p2_json = json.loads(p2)
        explanation = explain_changes(p1_json, p2_json)
        ############################################################################################
        print(explanation)
        win['res'].update(explanation)

    if event == 'Generate Query Plan':
        if not explain:
            sg.Popup("Please Connect to Database")
            continue

        q1 = values['q1']
        q2 = values['q2']

        if q1:
            try:
                p1 = explain.get_plan(q1)
                json_formatted_str_p1 = json.dumps(p1, indent=2)
                win['p1'].update(json_formatted_str_p1)
            except:
                sg.Popup("Please check Query 1's format")

        if q2:
            try:
                p2 = explain.get_plan(q2)
                json_formatted_str_p2 = json.dumps(p2, indent=2)
                win['p2'].update(json_formatted_str_p2)
            except:
                sg.Popup("Please check Query 2's format")

    if event == 'Visualise Query Plan':
        p1 = values['p1']
        p2 = values['p2']
        win['img_tab'].select()

        if p1:
            fig1, ax1 = plt.subplots()
            text1, ax1 = visualise_qep(json.loads(p1), ax1)
            win['tree1'].update(text1)
            canvas1 = FigureCanvasTkAgg(fig1, win['canvas1'].Widget)
            plot_widget1 = canvas1.get_tk_widget()
            plot_widget1.grid(row=0, column=0)
            canvas1.draw()

        if p2:
            fig2, ax2 = plt.subplots()
            text2, ax2 = visualise_qep(json.loads(p2), ax2)
            win['tree2'].update(text2)
            canvas2 = FigureCanvasTkAgg(fig2, win['canvas2'].Widget)
            plot_widget2 = canvas2.get_tk_widget()
            plot_widget2.grid(row=0, column=0)
            canvas2.draw()
        win.finalize().maximize()
        # gui.visualise_graph(p1)

    if event == 'Reset':
        gui.reset(win)
        if ax1:
            ax1.clear()
            ax1.axis('off')
            canvas1.draw()
        if ax2:
            ax2.clear()
            ax2.axis('off')
            canvas2.draw()

    if event == sg.WIN_CLOSED:
        break


