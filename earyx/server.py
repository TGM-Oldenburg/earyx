import earyx.exception as expt
from tornado.websocket import WebSocketHandler
from tornado.web import Application, RequestHandler
import earyx.exception
import tornado.web
from tornado.ioloop import IOLoop
import uuid
import re
import os
import json
import time
import sounddevice as sd
import matplotlib.pyplot as plt
from io import BytesIO
import inspect
import sys
import numpy as np
import soundfile as sf
import struct
import numpy
import socket

def to_bytes(n):
    return struct.pack("@i", n)

class EaryxServer(Application):

    def __init__(self, path_to_exps=None):
        if path_to_exps:
            self.eh = ExperimentHandler(path_to_exps)
        else:
            self.eh = ExperimentHandler()
        
        dirnam = os.path.dirname(__file__)
        settings = {
            'static_path': os.path.join(dirnam, 'gui'),
            'template_path': os.path.join(dirnam, 'gui'),
        }
        handlers = [
            (r"/", IndexHandler, dict(eh=self.eh)),
            (r"/select/", SelectHandler, dict(eh=self.eh)),
            (r"/earyx/(.*)", EchoWebSocket, dict(eh=self.eh)),
            (r"/active/", ActiveHandler, dict(eh=self.eh))
        ]

        Application.__init__(self,handlers, **settings)

class SelectHandler(RequestHandler):

    def initialize(self, eh):
        """ makes experiment available for websocket server

        This method makes avaible the functions that belong to the
        :class:`Experiment` class.

        Parameters
        ----------
        exp : :class:`Experiment`
        """
        self.__eh = eh

    
    def get(self):
        try:
            cid = self.get_argument("cid")
        except tornado.web.MissingArgumentError:
            self.redirect('/')
        etype = self.__eh.get_experiment_type(cid)

        if isinstance(etype, int):
            filename = '{}_afc_gui.html'.format(etype)
        else:
            filename = 'matching_gui.html'
        self.render(filename, clientid=cid)

class ActiveHandler(RequestHandler):
    
    def initialize(self, eh):
        """ makes experiment available for websocket server

        This method makes avaible the functions that belong to the
        :class:`Experiment` class.

        Parameters
        ----------
        exp : :class:`Experiment`
        """
        self.__eh = eh

    def get(self):
        self.render('active.html', active=self.__eh.exps)


class ExperimentHandler():

    def __init__(self, exp_path=os.path.abspath(os.path.join(
            os.path.dirname(__file__),"experiments"))):
        self.exps = {}
        self.aviable_exps = {}
        self.exp_path = exp_path
        sys.path.insert(0,self.exp_path)
        self.load_experiments()
        del sys.path[0]

    def load_experiments(self):
        for root, dirs, files in os.walk(self.exp_path, topdown=False):
            for name in files:
                if name[-3:] == ".py":
                    e_name = name[:-3]
                    name = name[:-3]
                    self.aviable_exps[e_name] = __import__(e_name, locals(), globals())


    def get_experiment_names(self):
        return self.aviable_exps.keys()
                
        
    def add_existing_experiment(self, exp, debug, audio):
        cid = uuid.uuid4().hex
        if cid not in self.exps:
            self.exps[cid] = {}
            self.exps[cid]['exp'] = exp
            self.exps[cid]['debug'] = debug
            self.exps[cid]['audio'] = audio
            self.exps[cid]['started'] = False
        return cid

    def get_experiment_type(self,cid):

        if hasattr(self.exps[cid]['exp'], 'num_afc'):
            return self.exps[cid]['exp'].num_afc
        else:
            return 'matching'

    def remove_client(self, cid):
        print('Remove client with id:',cid)
        del self.exps[cid]
        if not self.exps:
            print('Stop server...')
            IOLoop.instance().stop()

    
class IndexHandler(RequestHandler):
    
    def initialize(self, eh):
        self.__eh = eh

    def get(self):
        try:
            name = self.get_argument("name")

        except tornado.web.MissingArgumentError:
            exps = self.__eh.get_experiment_names()
            self.render('index.html', experiments=list(exps))
            return
                
        

    def post(self):
        name  = self.get_argument('experiment')
        try:
            debug = self.get_argument('debug')
            deb = True
        except:
            deb = False
        print('debug:',deb)
        module = self.__eh.aviable_exps[name]
        classname = self._to_camelcase(name)
        exp = getattr(module, classname)()
        cid = self.__eh.add_existing_experiment(exp,deb,1)
        self.redirect('/select/?cid='+cid)

        
    def _to_camelcase(self, s):
        e = re.sub(r'(?!^)_([a-zA-Z])', lambda m: m.group(1).upper(), s)
        return e[0].upper()+e[1:]
            
            


class EchoWebSocket(WebSocketHandler):
    """This class builds a websocket server and handles the incoming and outgoing
    events from and to the GUI.

    Parameters
    ----------
    WebSocketHandler : :class:`WebSocketHandler`

    """
    
    def initialize(self, eh):
        """ makes experiment available for websocket server

        This method makes avaible the functions that belong to the
        :class:`Experiment` class.

        Parameters
        ----------
        exp : :class:`Experiment`
        """
        self.__eh = eh
        self.exp = None
        self.terminated = False
        self.run = None
     
    def open(self, client_id):
        print("WebSocket opened")
        self.cid = client_id
        self.exp = self.__eh.exps[self.cid]['exp']
        self.debug = self.__eh.exps[client_id]['debug']
        self.audio_flag = self.__eh.exps[client_id]['audio']
        if self.__eh.exps[client_id]['started'] == False:
            if hasattr(self.exp, 'description'):
                self.write_message({'type':'desc', 'content':self.exp.description})
            if self.exp.allow_debug:
                self.write_message({'type': 'debug_state', 'content': self.exp.debug})
            self.write_message({'type':'name','content': self.exp.subject_name})
        self.__eh.exps[client_id]['started'] = True
        self.write_message({'type': 'allow_plot', 'content': self.exp.allow_debug})
  
    def on_message(self, message):
        """ sends and receives signals to and from the websocket client

        This method is the main method of a GUI-aided experiment, as it analyses the
        incoming events. It receives button clicks and executes the respective
        code. In this way an answer is set, a new run is started or the experiment
        gets quit. 

        Parameters
        ----------
        message : JSON struct

        Returns
        -------
        no return arguments, but sends messages to the client
        """
        ans_type = json.loads(message)['type']
        answer = json.loads(message)['content']

        if ans_type == "start_signal":
            self.write_message({'type':'params',  #'params' for correct printing pos
                                'content':'starting experiment...'})
            time.sleep(2)
            self.write_message({'type':'feedback', 'content':' '})
            self.run, self.trial = self.present_next_trial()
        
        elif ans_type == 'answer':
            if not self.run:
                return
            self.exp.set_answer(self.run, self.trial, answer)
            self.send_message('audio', 'clear')
            if self.exp.feedback and hasattr(self.exp,'num_afc'):
                if self.trial.is_correct == True:
                    self.write_message({'type':'feedback', 'content':'correct'})
                else:
                    self.write_message({'type':'feedback',
                                        'content':'not correct'})
                time.sleep(1)                  # show feedback message for 1 sec
                self.write_message({'type':'feedback', 'content':' '}) # del msg
            try:
                self.exp.adapt(self.run)
            except expt.RunFinishedException:
                self.write_message({'type':'feedback',
                                    'content':'Run finshed'})
                self.write_message({'type':'run_finished',
                                    'content':'run_finished'})
                return
            except expt.RunStartMeasurement:
                self.write_message({'type': 'feedback',
                                    'content': 'start measurement phase'})
                time.sleep(1)                  # show feedback message for 1 sec
                self.write_message({'type':'feedback', 'content':' '}) # del msg

            if self.exp.allow_debug and self.exp.debug:
                    self.plot(self.run, self.exp.parameters)
                    
            self.run, self.trial = self.present_next_trial()
                
        elif ans_type == "next_run":
            self.exp.skip_run(self.run)
            self.send_message('feedback', 'Next run started')
            time.sleep(3)                          # show feedback message for 3 sec
            self.send_message('feedback', ' ') # del. feedb. msg
            
            try:
                self.run, self.trial = self.present_next_trial()
            except StopIteration:
                self.on_message(json.dumps({"type": 'quit',
                                            "content": 'save'}))
                
        elif ans_type == "quit":
            if answer == 'save':
                path = self.exp.finalize(True)
                self.write_message({'type': 'feedback', 'content':
                                    'Experiment saved as %s ... finished' % path})
            elif answer == 'drop':
                self.exp.finalize(False)
                self.write_message({'type': 'feedback', 'content':
                                    'Experiment was not saved! ...finished'})

            self.__eh.remove_client(self.cid)
            self.write_message({'type': 'quit',
                                'content': 'all_done'})
            
        elif ans_type == 'name':
            self.exp.subject_name = answer
       
        elif ans_type == 'cancel':
            pass

        elif ans_type == 'debug':
            if self.exp.allow_debug:
               self.exp.debug = not self.exp.debug
               state = "on" if self.exp.debug else "off"
               self.write_message({'type':'feedback',
                                   'content':"Debugging is '%s' now" % state})
            else:
               self.write_message({'type': 'feedback',
                                   'content': 'Debugging not allowed'})

        elif ans_type == 'terminate':
            self.terminated = True

    def send_message(self, msg_type, content, data=None):
        """Send a message.
        Arguments:
        msg_type  the message type as string.
        content   the message content as json-serializable data.
        data      raw bytes that are appended to the message.
        """

        if data is None:
            try:
                self.write_message(json.dumps({"type": msg_type,
                                           "content": content}).encode())
            except:
                pass
        else:
            header = json.dumps({'type': msg_type,
                                 'content': content}).encode()
            # append enough spaces so that the payload starts at an 8-byte
            # aligned position. The first four bytes will be the length of
            # the header, encoded as a 32 bit signed integer:
            header += b' ' * (8 - ((len(header) + 4) % 8))
            # the length of the header as a binary 32 bit signed integer:
            prefix = to_bytes(len(header))
            try:
                self.write_message(prefix + header + data, binary=True)
            except:
                pass

    def plot(self, runs, params):
        variables = [trial.variable for trial in runs.trials]
        length = len(variables)
        f = plt.figure(111)
        ax = f.add_subplot(111)
        f.clear()
        
        if runs.start_measurement_idx == None:
           x_axes = numpy.arange(1,length+1)
           plt.plot(x_axes,variables,'o--',markerfacecolor='k',markersize=5)
        else:
            x1 = numpy.arange(1,runs.start_measurement_idx+1)
            x2 = numpy.arange(runs.start_measurement_idx,length+1)
            measurement_variables = variables[runs.start_measurement_idx-1:]
            plt.plot(x1,variables[:runs.start_measurement_idx],'o--',markerfacecolor='k',markersize=5)
            plt.plot(x2,measurement_variables,'ob-',markersize=5)
            median_measurement = numpy.median(measurement_variables)
            std_measurement = numpy.std(measurement_variables)
            plt.text(0.7, 0.85,'Med:', ha='left', va='center',transform = ax.transAxes)
            plt.text(0.82, 0.85,round(median_measurement,2), ha='left', va='center',transform = ax.transAxes)
            plt.text(0.7, 0.77,'Std:', ha='left', va='center',transform = ax.transAxes)
            plt.text(0.82, 0.77,round(std_measurement,2), ha='left', va='center',transform = ax.transAxes)
        
        title_string = runs.get_param_string(params)
        plt.title(title_string)
        plt.xlabel('Number of trial')
        plt.ylabel('Variable value')
        plt.xlim((0,length+1))
        plt.ylim((min(variables)-1,max(variables)+1))
        figfile = BytesIO()
        f.savefig(figfile, format='svg')
        figdata_svg = figfile.getvalue().decode('utf-8')
        # figdata_svg = '<svg' + figfile.getvalue().decode('utf-8').split('<svg')[1]
        self.write_message({'type':'plot', 'content':figdata_svg})

        
    def on_close(self):
        print("WebSocket closed")

    def check_origin(self, origin):
        return True
        
    def present_next_trial(self):
            run = self.exp.next_run()
            string = run.get_param_string(self.exp.parameters)
            self.write_message({'type':'params', 'content': string})
            self.write_message({'type':'task', 'content':self.exp.task})
            trial, signal = self.exp.next_trial(run)
            self.present_signal(signal, trial.sample_rate)
            return run, trial

    def present_signal(self,signal, sample_rate):
        """Play back signal """
        signal = [np.tile(sig, (2, 1)).T for sig in signal
                  if len(sig.shape) == 1 ]
        if (self.audio_flag == 1 or self.audio_flag == 2):
            num_channels = signal[0].shape[0]
            signals = np.concatenate(signal)
            times = [part.size/num_channels/sample_rate for part in signal]
            temp_file = BytesIO()
            with sf.SoundFile(temp_file, mode='w', format='WAV',
                              samplerate=sample_rate,
                              channels=num_channels) as f:
                f.write(signals)
            self.send_message('play',times,temp_file.getvalue())

        if (self.audio_flag == 2 or self.audio_flag == 3):
            blink = False
            i = 1
            with sd.Stream(samplerate=sample_rate, dtype='float32') as s:
                for part in signal:
                    if self.audio_flag == 3:
                        if (self.exp.visual_indicator and hasattr(self.exp, 'num_afc')):
                            if blink:
                                self.write_message({'type':'but{}'.format(i),
                                                    'content':'red'})
                                i += 1
                            else:
                                self.write_message({'type':'but1',
                                                    'content':'white'})
                                self.write_message({'type':'but2',
                                                    'content':'white'})
                                self.write_message({'type':'but3',
                                                    'content':'white'})
                                self.write_message({'type':'but4',
                                                    'content':'white'})
                            blink = not blink
                    s.write(np.asarray(part, dtype='float32', order='C'))
                i = 1


                    
if __name__ == '__main__':
    app = EaryxServer()
    port = 8888
    app.listen(port)
    your_ip =  socket.gethostbyname(socket.gethostname())
    print('Type http://'+your_ip+""":8888 in your browser to connect to the experiment.
    \n (Server and client must be on the same network.)""")
    IOLoop.instance().start()
