import PySimpleGUI as sg

class Analyzer_GUI:
    def create_win(self):
        sg.theme("DarkBlue3")
        sg.set_options(font = 'Bahnschrift')
        samples = ["Test Case " + str(i) for i in range(len(self.get_sample_queries()))]

        col1_layout = [[sg.Text("Input Query 1:")],
                       [sg.Multiline(key='q1', size=(50,5))],
                       [sg.Text("Input Query Plan 1:")],
                       [sg.Multiline(key='p1', size=(50,8))],

                       ]
        col2_layout = [[sg.Text("Input Query 2:"),],
                       [sg.Multiline(key='q2', size=(50,5))],
                       [sg.Text("Input Query Plan 2:")],
                       [sg.Multiline(key='p2', size=(50, 8))],
                       ]

        exp_tab = sg.Tab('Explanation', [
            [sg.Multiline(key='res', expand_y=True, expand_x=True, disabled=True, size=(None, 20))],
        ], expand_y=True, expand_x=True, key='exp_tab')


        img_col = sg.Column([[
            sg.Column(
                [[sg.Text("Query Plan 1", size=(None, 2))], [sg.Push(), sg.Canvas(key='canvas1', size=(None, 800),), sg.Push()], [sg.Canvas(key='controls1')], [sg.Text(key='tree1')]],
                 expand_y=True, expand_x=True,
            ),
            sg.VSeparator(),
            sg.Column(
                [[sg.Text("Query Plan 2", size=(None, 2))], [sg.Push(), sg.Canvas(key='canvas2', size=(None, 800),), sg.Push()],[sg.Canvas(key='controls2')], [sg.Text(key='tree2')]],
                expand_y=True, expand_x=True,
            )
        ]],
        expand_y=True, expand_x=True, scrollable=True,vertical_alignment='center', vertical_scroll_only=True, size=(None, 800))

        img_tab = sg.Tab('Query Plan Diagram', [[img_col]], expand_y=True, expand_x=True, key='img_tab')

        win_layout = [
            [sg.Push(), sg.Text("CZ4031 QEP Analyser", font='Bahnschrift 30'), sg.Push()],
            [sg.Sizer(v_pixels=10)],
            [sg.Push(), sg.Button('Connect to PostgreSQL Database'), sg.Push()],
            [sg.Push(), sg.Combo(values=samples, key='samples', size=(20,1), readonly=True), sg.Combo(values=['Query 1', 'Query 2'], key='sam_q', size=(20,1), readonly=True, default_value='Query 1'),
             sg.Button('Test'), sg.Button("Reset", button_color='red'), sg.Push()],
            [sg.Sizer(v_pixels=40)],
            [sg.Push(), sg.Column(col1_layout), sg.VSeparator(), sg.Column(col2_layout), sg.Push(),],
            [sg.Sizer(v_pixels=10)],
            [sg.Push(), sg.Button("Generate Explanation"), sg.Sizer(h_pixels=20), sg.Button("Generate Query Plan"), sg.Sizer(h_pixels=20), sg.Button("Visualise Query Plan"), sg.Push()],
            [sg.Text("Rsults:", font='Bahnschrift 25')],
            [sg.TabGroup([[exp_tab, img_tab]], expand_y=True, expand_x=True)],
        ]
        win_layout = [[sg.Column(win_layout, vertical_scroll_only=True, scrollable=True, vertical_alignment='center', expand_y=True, expand_x=True, key='final_col')]]

        window = sg.Window("Demo", win_layout, resizable=True)
        window.finalize().maximize()

        return window

    def clear_toolbar(self, tool_canvas):
        if tool_canvas.children:
            for child in tool_canvas.winfo_children():
                if child.mode:
                    sg.Popup("Deselect toolbar")
                    return False
                child.destroy()
        return True

    def get_sample_queries(self):
        samples = [
                #     "select * from public.customer",
                #    "select * from public.customer limit 100",
                #    """select C.c_name, C.c_address, O.o_totalprice
                #       from public.customer as C join public.orders as O on C.c_custkey = O.o_custkey
                #       where C.c_acctbal < 5000
                #       limit 100"""
                    "select n_nationkey from nation, region",
                    "select n_nationkey from nation join region on nation.n_regionkey = region.r_regionkey"
                   ]
        return samples

    def get_connection_string(self):
        text = sg.PopupGetText('Please enter connection string for connecting to PostgreSQL Database \n\nFormat: dbname=<enter database name> user=<enter username> password=<enter password> (no commas)', title="Connection String")
        return text

    def reset(self, win):
        win['q1'].update('')
        win['q2'].update('')
        win['p1'].update('')
        win['p2'].update('')
        win['res'].update('')

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

