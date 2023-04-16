from interface import Analyzer_GUI
import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from explain import Explain, explain_changes, visualise_qep
import json

## Initialise
gui = Analyzer_GUI()
win = gui.create_win()

explain = None
ax1 = None
ax2 = None
canvas1 = None
canvas2 = None

## Run the GUI
while True:
    event, values = win.read()
    if event == 'Connect to PostgreSQL Database':
        connection_string = gui.get_connection_string() # connection_string format: "db_name=<> user=<> password=<>" (no commas)
        try:
            explain = Explain(connection_string)
        except:
            sg.Popup("Connection Failed")
        print("conn", connection_string)

    if event == 'Test':
        samples = gui.get_sample_queries()
        samples_ind = int(values['samples'].split(" ")[-1]) - 1
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

        p1_json = json.loads(p1)
        p2_json = json.loads(p2)
        
        try:
            explanation = explain_changes(p1_json, p2_json)
            print(explanation)
            win['res'].update(explanation)  
        except ValueError:
            sg.Popup("Error: The difference between the query plans is too large")


    if event == 'Generate Query Plan':
        if not explain:
            sg.Popup("Please Connect to Database")
            continue

        q1 = values['q1']
        q2 = values['q2']

        p1 = explain.get_plan(q1)
        p2 = explain.get_plan(q2)

        if (not p1) and (not p2):
            sg.Popup("Please check the format of Query 1 & 2")
            continue
            
        if p1:
            json_formatted_str_p1 = json.dumps(p1, indent=2)
            win['p1'].update(json_formatted_str_p1)
        elif q1:
            sg.Popup("Please check Query 1's format")

        if p2:
            json_formatted_str_p2 = json.dumps(p2, indent=2)
            win['p2'].update(json_formatted_str_p2)
        elif q2:
            sg.Popup("Please check Query 2's format")


    if event == 'Visualise Query Plan':
        p1 = values['p1']
        p2 = values['p2']
        win['img_tab'].select()

        ## set fig1
        mode1 = gui.clear_toolbar(win['controls1'].TKCanvas)
        if mode1 is False: continue
        fig1 = Figure(figsize=(5, 6))
        # fig1.subplots_adjust(0,0,1,1,0,0)
        fig1.subplots_adjust(hspace=0, wspace=0)
        ax1 = fig1.add_subplot(1, 1, 1)
        ax1.axis('off')
        canvas1 = FigureCanvasTkAgg(fig1, win['canvas1'].Widget)
        plot_widget1 = canvas1.get_tk_widget()
        plot_widget1.grid(row=0, column=0)
        canvas1.draw()

        ## set fig2
        mode2 = gui.clear_toolbar(win['controls2'].TKCanvas)
        if mode2 is False: continue
        fig2 = Figure(figsize=(5, 6))
        fig2.subplots_adjust(0,0,1,1,0,0)
        ax2 = fig2.add_subplot(1, 1, 1)
        ax2.axis('off')
        canvas2 = FigureCanvasTkAgg(fig2, win['canvas2'].Widget)
        plot_widget2 = canvas2.get_tk_widget()
        plot_widget2.grid(row=0, column=0)
        canvas2.draw()

        if p1:
            text1, ax1 = visualise_qep(json.loads(p1), ax1)
            win['tree1'].update(text1)
            toolbar1 = NavigationToolbar2Tk(canvas1, win['controls1'].TKCanvas)
            toolbar1.update()
            canvas1.draw()

        if p2:
            text2, ax2 = visualise_qep(json.loads(p2), ax2)
            win['tree2'].update(text2)
            toolbar1 = NavigationToolbar2Tk(canvas2, win['controls2'].TKCanvas)
            toolbar1.update()
            canvas2.draw()

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


