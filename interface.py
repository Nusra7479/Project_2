import PySimpleGUI as sg

class Analyzer_GUI:
    def create_win(self):
        sg.theme("DarkBlue3")
        sg.set_options(font = 'Bahnschrift')

        col1_layout = [[sg.Text("Input Query 1:")],
                       [sg.Multiline(key='q1', size=(50,5))],
                       [sg.Text("Input Query Plan 1:")],
                       [sg.Multiline(key='p1', size=(50,5))],

                       ]
        col2_layout = [[sg.Text("Input Query 2:"),],
                       [ sg.Multiline(key='q2', size=(50,5))],
                       [sg.Text("Input Query Plan 2:")],
                       [sg.Multiline(key='p2', size=(50, 5))],
                       ]

        win_layout = [
            [sg.Push(), sg.Text("CZ4031 QEP Analyser", font='Bahnschrift 30'), sg.Push()],
            [sg.Push()],
            [sg.Push(), sg.Column(col1_layout), sg.VSeparator(), sg.Column(col2_layout), sg.Push(),],
            [sg.Push()],
            [sg.Push(), sg.Button("Generate Explanation"), sg.Sizer(h_pixels=20), sg.Button("Generate Query Plan"), sg.Sizer(h_pixels=20), sg.Button("Visualise Query Plan"), sg.Push()],
            [sg.Push(), sg.Text("Explanation:", font='Bahnschrift 25', size=(120, 1)), sg.Push()],
            [sg.Text(key='res')]
            # [sg.Frame(
            #     '',
            #     [[sg.Text(key='res')]],
            #     border_width=1,
            # )],
        ]

        window = sg.Window("Demo", win_layout)
        window.finalize().maximize()

        return window

    def preview_fonts(self):
        '''
            Demo Font Previewer

            Gets a list of the installed fonts according to tkinter.
            Requires PySimpleGUI version 4.57.0 and newer (that's when sg.Text.fonts_installed_list was added)

            Uses the Text element's class method to get the fonts reported by tkinter.

            Copyright 2020, 2021, 2022 PySimpleGUI
        '''

        fonts = sg.Text.fonts_installed_list()

        sg.theme('Black')

        layout = [[sg.Text('My Text Element',
                           size=(20, 1),
                           click_submits=True,
                           relief=sg.RELIEF_GROOVE,
                           font='Courier` 25',
                           text_color='#FF0000',
                           background_color='white',
                           justification='center',
                           pad=(5, 3),
                           key='-text-',
                           tooltip='This is a text element',
                           )],
                  [sg.Listbox(fonts, size=(30, 20), change_submits=True, key='-list-')],
                  [sg.Input(key='-in-')],
                  [sg.Button('Read', bind_return_key=True), sg.Exit()]]

        window = sg.Window('My new window', layout)

        while True:  # Event Loop
            event, values = window.read()
            if event in (sg.WIN_CLOSED, 'Exit'):
                break
            text_elem = window['-text-']
            print(event, values)
            if values['-in-'] != '':
                text_elem.update(font=values['-in-'])
            else:
                text_elem.update(font=(values['-list-'][0], 25))
        window.close()

    def main(self):
        win = self.create_win().finalize()
        win.maximize()
        while True:
            event, values = win.read()
            if event == 'Generate Explanation':
                q1 = values['q1']
                p1 = values['p1']
                q2 = values['q2']
                p2 = values['p2']
                win['res'].update("Q1: "+ q1 + "\nQ2: "+ q2 + "\np1 " + p1 + "\np2 "+ p2)

            if event == sg.WIN_CLOSED:
                break

