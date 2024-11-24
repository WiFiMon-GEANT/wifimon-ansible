from dash import Dash, dcc, html, Input, Output, callback
import subprocess
from dash.exceptions import PreventUpdate
from time import sleep

def get_wts_info():
    with open("wts_info.txt") as line:
        wts_info = line.read()
        return wts_info

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
        wts_info = get_wts_info()

        return html.Div([
            html.P("Select the desired WiFiMon Hardware Probe:", style = {"font-weight" : "bold"}),
            dcc.Dropdown(probe_names, probe_names[0], id = 'probe_dropdown'),
            html.P("Select the command that you want to execute:", style = {"font-weight" : "bold"}),
            dcc.Dropdown(["ping", "traceroute", "default route", "interfaces"], "ping", id = 'command_dropdown'),
            html.P("Select the argument of the command:", style = {"font-weight" : "bold"}),
            dcc.Dropdown(["1.1.1.1", "8.8.8.8", "9.9.9.9", wts_info], "1.1.1.1", id = 'argument_dropdown'),
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
    Input('command_dropdown', 'value'),
    Input('argument_dropdown', 'value'), 
    Input('button', 'n_clicks')]
)
def update_output(probe, command, argument, n_clicks):
    if n_clicks == None:
        raise PreventUpdate
    else:
        sleep(7)
        if command == "ping":
            to_execute = "salt '" + str(probe) + "' network.ping " + str(argument)
        elif command == "traceroute":
            to_execute = "salt '" + str(probe) + "' network.traceroute " + str(argument)
        elif command == "default route":
            to_execute = "salt '" + str(probe) + "' network.default_route"
        elif command == "interfaces":
            to_execute = "salt '" + str(probe) + "' network.interfaces"
        output = return_command_output(to_execute).decode('utf8')
        return output

if __name__ == '__main__':
    app.run(port = 8889)
