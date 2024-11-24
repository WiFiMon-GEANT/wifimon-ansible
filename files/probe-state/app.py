from dash import Dash, dcc, html, Input, Output, callback
import subprocess
from dash.exceptions import PreventUpdate
from time import sleep

def return_command_output(command):
    proc = subprocess.Popen(command, stdout = subprocess.PIPE, shell = True)
    (out, err) = proc.communicate()
    output = out.rstrip('\n'.encode('utf8'))
    return output

app = Dash(__name__)

def support_layout():
    command = "salt '*' test.ping"
    active_probes = return_command_output(command).decode('utf8')
    active_probes = active_probes.replace(" ", "").split("\n")
    try:
        probe_names = [active_probes[i][:-1] for i in range(0, len(active_probes), 2) if active_probes[i + 1] == "True"]

        return html.Div([
            html.P("These are the active WiFiMon Hardware Probes! Check the running version of a specific probe:", style = {"font-weight" : "bold"}),
            dcc.Dropdown(probe_names, probe_names[0], id = 'probe_dropdown'),
            html.Button('Submit', id = 'button'),
            html.Div([
                html.P(id = 'dd-output-container')
                ])
            ])
    except:
        return html.P("No probes available")

app.layout = support_layout
@callback(
    Output('dd-output-container', 'children'),
    [Input('probe_dropdown', 'value'),
    Input('button', 'n_clicks')]
)
def update_output(probe, n_clicks):
    if n_clicks == None:
        raise PreventUpdate
    else:
        sleep(4)
        to_execute = "salt '" + str(probe) + "' cmd.run 'cat version.txt'"
        output = return_command_output(to_execute).decode('utf8')
        return output

if __name__ == '__main__':
    app.run(port = 8890)
