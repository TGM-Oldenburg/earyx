import sounddevice as sd
import earyx.server as svr
import earyx.exception as expt
import matplotlib.pyplot as plt
from tornado.ioloop import IOLoop
import json
import time
import webbrowser as wb
import os
import os.path
from io import BytesIO
import soundfile as sf
import struct
import numpy as np
import numpy




class Ui():

    def __init__(self, experiment, extern=False, debug=True, audio_flag=1):
        self.extern = extern
        self.debug = experiment.debug
        self.audio_flag = audio_flag
        self.start(experiment)

        
    def start(self, exp):
        raise NotImplemented

    
class Tui(Ui):

    welcome_screen = """                                                                   
                                                                   
         __.....__                                                 
     .-''         '.                .-.          .-                
    /     .-''"'-.  `.         .-,.--\ \        / /                
   /     /________\   \   __   |  .-. \ \      / ____     _____    
   |                  |.:--.'. | |  | |\ \    / `.   \  .'    /    
   \    .-------------/ |   \ || |  | | \ \  / /  `.  `'    .'     
    \    '-.____...---`" __ | || |  '-   \ `  /     '.    .'       
     `.             .' .'.''| || |        \  /      .'     `.      
       `''-...... -'  / /   | || |        / /     .'  .'`.   `.    
                      \ \._,\ '|_|    |`-' /    .'   /    `.   `.  
                       `--'  `"        '..'    '----'       '----'
------------------------------------------------------------------
    """

    
    def start(self, exp):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.message(self.welcome_screen)
        self.message("Your experiment:" + exp.cls+ "\n")
        if exp.subject_name == '':
            exp.subject_name = input("To start, please type your name or abbreviation: ")
        self.message("\n"+exp.description+"\n")
        if not self.confirm('Start experiment'):
            return
        while True:
            try:
                run = exp.next_run()
            except StopIteration:
                self.message("Experiment finished")
                self.save(exp)
                return
            trial, signal  = exp.next_trial(run)
            self.present_signal(signal, trial.sample_rate)
            while trial.answer == None:
                try:
                    answer = self.get_user_response(exp.task)
                except expt.RunAbortException:
                    exp.skip_run(run)
                    break
                except expt.ExperimentAbortException:
                    self.save(exp)
                    self.message("\nquit experiment")
                    return
                except expt.ToggleDebugException:
                    if exp.allow_debug:
                        self.debug = not self.debug
                        state = "on" if self.debug else "off"
                        self.message("\nPlotting is '%s' now" % state)
                    else:
                        self.message("\nPlotting is disabled")
                    continue
                try:
                    answer = exp.check_answer(answer)
                except expt.WrongAnswerFormat as e:
                    self.warning(e.msg)
                    continue
                else:
                    exp.set_answer(run, trial, answer)
                    if exp.feedback and hasattr(exp,'num_afc'):
                        (self.message('correct') if trial.is_correct
                         else self.message('not correct'))
                    try:
                        exp.adapt(run)
                    except expt.RunFinishedException:
                        if self.confirm("\nRun completed. Continue?"):
                            continue
                        else:
                            self.save(exp)
                            self.message("\nquit experiment")
                            return
                    except expt.RunStartMeasurement:
                        self.message('\nStart measurement phase')
                if exp.allow_debug and self.debug:
                    self.plot(run, exp.parameters)

    def save(self, exp):
        if self.confirm("Save experiment state?"):
            path = exp.finalize(True)
            self.message("Experiment saved as %s" % path)
        else:
            exp.finalize(False)

    def present_signal(self,signal, sample_rate):
        """Play back signal """
        signal = [np.tile(sig, (2, 1)).T for sig in signal
                  if len(sig.shape) == 1 ]
        with sd.Stream(samplerate=sample_rate, dtype='float32') as s:
            for part in signal:
                s.write(np.asarray(part, dtype='float32', order='C'))


    def get_user_response(self, task):
        print ('\r')
        ans = input(task)
        if ans == 'n':
            if self.confirm("\nReally skip run?"):
                raise expt.RunAbortException
        elif ans == 'q':
            if self.confirm("\nReally quit experiment?"):
                raise expt.ExperimentAbortException
        elif ans == 'g':
            raise expt.ToggleDebugException
        else:
            return ans
    
    def confirm(self, quest):
        ans = input(quest+" (y/n)")
        if ans == "y":
            return True
        else:
            return False

    def warning(self, msg):
        print("\nWARNING:", msg)

    def message(self, msg):
        print(msg)

    def plot(self, runs, params):
        variables = [trial.variable for trial in runs.trials]
        length = len(variables)
        plt.ion()
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
        plt.show()
        plt.draw()


class Gui(Ui):

    def start(self, exp):

        app = svr.EaryxServer()
        cid = app.eh.add_existing_experiment(exp, self.debug, self.audio_flag)
        port = 8888
        app.listen(port)
        if not self.extern:
            wb.open('http://localhost:8888/select/?cid='+cid)
        IOLoop.instance().start()

class Model(Ui):

    def __init__(self, model_func):
        self.model_func = model_func
        
    
    def start():
        while True:
            try:
                run = exp.next_run()
            except StopIteration:
                exp.finalize(True)
                return
            trial, signal = exp.next_trial(run)
            answer = self.model_func(signal)
            try:
                answer = exp.check_answer(answer)
            except expt.WrongAnswerFormat as e:
                self.waring(e.msg)
                return
            try:
                exp.set_answer_and_adapt(run, trial, answer)
            except expt.RunFinishedException:
                continue
            if exp.debug:
                self.plot(run.trials)
