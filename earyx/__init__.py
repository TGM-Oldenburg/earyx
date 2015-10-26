import argparse
import socket
from . import ui

def start(class_name):
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-u','--ui',
                        help = 'select UI (terminal/ gui/ egui) deflaut: terminal',
                        default = 'terminal',
                        dest = 'ui')
    parser.add_argument('-l','--l',
                        help = 'flag for loading experiment',
                        action = 'store_true',
                        dest = 'load',
                        default = False)
    parser.add_argument('-a','--audio',
                        help = """audio states\n
                        1: audio only on gui\n
                        2: audio on gui and server\n
                        3: audio only on server""",
                        default = 3,
                        dest = 'audio_flag')
    args = parser.parse_args()

    experiment = class_name()

    args.audio_flag = int(args.audio_flag)

    if args.load:
        experiment.load()
        
    if str.lower(args.ui) == 'gui':
        ui.Gui(experiment, audio_flag = 3)
    if str.lower(args.ui) == 'terminal':
        ui.Tui(experiment)
    if str.lower(args.ui) == 'egui':
        your_ip =  socket.gethostbyname(socket.gethostname())
        print('Type http://'+your_ip+':8888/active/ in your browser to connect to the experiment.\n (Server and client must be on the same network.)')
        ui.Gui(experiment, extern = True, audio_flag = args.audio_flag)


