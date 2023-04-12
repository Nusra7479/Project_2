from interface import Analyzer_GUI
import PySimpleGUI as sg
import explain

gui = Analyzer_GUI()
win = gui.create_win()
while True:
    event, values = win.read()
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
        q1 = values['q1']
        q2 = values['q2']

        # p1 = explain.get_explain(q1)
        # p2 = explain.get_explain(q2)
        p2 = 'sample 1'
        p1 = 'sample 2'

        win['p1'].update(p1)
        win['p2'].update(p2)

    if event == sg.WIN_CLOSED:
        break

