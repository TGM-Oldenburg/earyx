"""This module contains experiment classes for earyx experiments.
In class :class:`Experiment` methods and attributes are defined which are the same for
all types of experiment.
Class :class:`AFCExperiment` and :class:`MatchingExperiment` inherit from
:class:`Experiment` and implement the interface like methods defined in this class.

It is part of the earyx toolbox for psychoacoustic experiments. 
"""
import random
from itertools import product
import earyx.adapt
import earyx.exception as expt
from earyx.run import Run
from earyx.trial import Trial
from earyx.saveload import SaveLoad
import datetime
import time
import numpy as np


class Experiment():
    """
    Base class of all earyx experiments

    This class provides the base methods and data structures for all
    experiments built with earyx but it is never directly instanciated
    because some methods are just "Interfaces"
    
    Attributes
    ----------
    subject_name : str
        name or abbrevation of test subject
    runs : list
        becomes list of :class:`Run`. This list is auto generated while
        experiment creation
    parameters : dict
        becomes dict of dict containing name, values, unit and description. For
        simple parameter handling there is the method :func:`add_parameter`.
        There must be at least one parameter in each experiment.
    variable : dict
        needs to contain name (string), value, unit (string). For simple variable
        handling there is the mdthod :func:`set_variable`. Each experiment
        has exactly one variable.
    adapt_settings : list
        list of adapt settings used in the experiment. For simple adapt settings
        handling there is the method :func:`add_adapt_setting`. There must be
        at least one adapt setting in each experiment.
    pre_signal : numpy array, float or tuple (optional)
        Signal part played before each trial. There are some options for simple
        signal generation. For more information see documentation section:
        `Zero signals`
    reference_signal : numpy array, list of numpy arrays
        Signal part(s) not containing the test sequence. In case of N-AFC experiment
        this can also an list of N-1 signals, which are randomly spread of the
        N-1 reference intervals *not* containing the test sequence.
    between_signal : numpy array, float or tuple (optional)
        Signal played between each signal part. Most of the time this variable is
        used for silence between the signal parts. For that rason it can be
        initialized as float or tuple. For more information, see documentation
        section: `Zero signals`. If not specified, singnal parts are simply joined
        together
    test_signal : numpy array
        Signal part containing the test sequence. 
    post_signal : numpy array, float or tuple (optional)
        if specified, this signal part is played at the end of trial.
    allow_debug : boolean (optional)
        With this variable the experiment creator can specify whether the
        test subject is  allowed to enable plotting or not. default: True
    discard_unfinished_runs : boolean (optional)
        Usually unfinished runs ar not saved when experiment is interrupted.
        With this flag set to **True** the test subjuct is able to continue
        unfinished runs later. Default: False
    sample_rate : int (optional)
        sampling frequency for all signals of the whole experiment. Default: 48000 
    calib : int or float (optional)
        This variable is a place holder for a calibration value. It can be used
        as factor or summand to fit the signal loudness to the test system settings.
        Without explicit usage in your signal generation this value has no impact
        on the signals. Default: 0.
    task : str
        Description of experiment and description of what the test subjects have
        to do. This message is displayed befor the experimetn starts.
    """

    def __init__(self):
        """initialization of the experiment

        In this method experiment initialization takes place. Start date ist set,
        default values are set, user defined init_experiment method is called
        and the list of runs is generated from given parameters and adapt settings.
        """
        self.cls = type(self).__name__
        self._create_time = datetime.datetime.now().strftime('%Y-%m-%dT%H.%M.%S')
        self.subject_name = ''
        self._sl = SaveLoad(self)
        self.runs = []
        self.parameters = {}
        self.variable = {}
        self.adapt_settings = []
        self.signals = {}
        self.pre_signal = []
        self.reference_signal = []
        self.between_signal = []
        self.test_signal = []
        self.post_signal = []
        self._save_names = {}
        self.allow_debug = True
        self.discard_unfinished_runs = True
        self.sample_rate = 48000
        self.calib = 0
        self.feedback = True
        self.debug = True
        self.visual_indicator = True
        self.init_experiment(self)
        self.time_to_signal(self)
        self._sl.unify_signals(self)
        self._generate_runs()

    def init_experiment(self, experiment):
        """method to init experiment wide settings.

        This method is called only once at the beginning of experiment. All settings
        with experiment wide validity should be defined here.
        """
        raise NotImplemented

    def _generate_runs(self):
        outer_param_list = []
        for name, parameter  in self.parameters.items():
            inner_param_list = [{name:value} for value in parameter["values"]]
            outer_param_list.append(inner_param_list)

        combinations = list(product(self.adapt_settings,*outer_param_list))
           
        for combi in combinations:
            params = {}
            for param in combi[1:]:
                params.update(param)

            adapt_settings = combi[0]
            AdaptClass = getattr(earyx.adapt,
                                      "Adapt%s" % adapt_settings["type"])
            RunClass = type('Run'+adapt_settings["type"],(Run,AdaptClass,),{})
            run = RunClass(params, self.variable["start_val"],
                                 adapt_settings, self.reference_signal,
                                 self.pre_signal, self.between_signal,
                                 self.post_signal, self.sample_rate, self.calib)
            
            self.init_run(run)
            self.time_to_signal(run)
            self.runs.append(run)
            self._sl.unify_signals(run)

    def add_parameter(self,name,values,unit,description=""):
        """Adds a new parameter to the experiment.

        This method offers a simple way to add a new parameter to the experiment.
        Usually this method is used in :func:`init_experiment`. To add more
        than one parameter this method can be called multiple times.

        Parameters
        ----------
        name : str
            name of the parameter. It **must not** contain any white space!!
        values : list
            list of all values of an parameter. If the parameter only contains
            one value it must be a list with one element
        unit : str
            unit of the parameter
        description : str (optional)
            short description
        
        Examples
        --------
        this.add_parameter(name='noise_level',values=[-60, -40, -20], unit='dB')

         .. note:: 
        
            The name must not contain any white space because
            in runs and trials the run specific value of this parameter can be
            referenced by its name.
        """        
        values = list(values)
        new_param = {"values": values, "unit": unit, "desc": description}
        self.parameters[name] = new_param

    def set_variable(self, name, start_val, unit, description=""):
        """Stes the variable of the experiment.

        This method offers a simple way to set the variable of the experiment.
        Usually this method is called in :func:`int_experiment`. Because every
        experiment has only one variable it can be called only once.
        
        Parameters
        ----------
        name : str
            name of the variable.
        start_val : int
            start value of the variable
        unit : str
            unit of the parameter            
        description : str (optional)
            short description

        Examples
        --------
        this.set_variable(name='frequency', start_val=1000, unit="Hz")
        """        
        var = {"name": name, "unit": unit, "start_val": start_val,
               "desc": description}
        self.variable = var

    def add_adapt_setting(self, adapt_method="1up2down", max_reversals=6,
                          start_step=5, min_step=1, **kwargs):
        """Add adapt method/setting.

        This method adds a adaption method and its start values to the experiment. 
                
        Parameters
        ----------
        adapt_method : str
            a number of adapt methods is pre-implemented:
            1up2down
            2up1down
            1up3down
            WUD (weighted up down)
        max_reversals : int
            number of reversals the trial is running
        start_step : int
            start step how the variable is changing            
        min_step : int 
            min step, if reached trial goes on for max_reversals
        kwargs : dict (optional)
            dict of keywords and arguments may used for special adapt method
            WUD needs key: pc_convergence  value: float 0..1
        """
        new_adapt = {"type": adapt_method, "max_reversals": max_reversals,
                     "start_step": start_step, "minstep": min_step}
        new_adapt.update(kwargs)
        self.adapt_settings.append(new_adapt)

    def build_signal(self):
        """ specific build is made by  method of the different experiment classes.
        """
        raise NotImplemented

    def check_answer(self):
        """ specific answer check is made by method of the different experiment classes.
        """
        raise NotImplemented

    def set_answer(self, run, trial, answer):
        """Depending on the given answer a new step is calculated by an adapt method.
                        
        Parameters
        ----------
        run : :class:`Run`
        trial : :class:`Trial`
        answer : int or str
        
        """
        trial.answer = answer
        trial.is_correct = trial.answer == trial.correct_answer
        run.trials.append(trial)

    def adapt(self, run):
        """ apply selected adapt rule to variable"""
        try:
            step = run.adapt(run.trials)
        except expt.RunFinishedException:
            run.finished = time.strftime('%d-%b-%Y__%H:%M:%S')
            if self.discard_unfinished_runs:
                for tr in run.trials:
                    self._sl.unify_signals(tr)
                self._sl.update_struct()
            raise
        run.variable += step
        if not self.discard_unfinished_runs:
            self._sl.unify_signals(run.trials[-1])
            self._sl.update_struct()
        if abs(step) == run.minstep and not run.start_measurement_idx:
            run.start_measurement_idx = len(run.trials)
            if not self.discard_unfinished_runs:
                self._sl.update_struct()
            raise expt.RunStartMeasurement
        

    def load(self):
        """ load experiment

        After experiment initialization a saved experiment can be loaded.
        This method is only a wrapper for the load method of the _sl attribute,
        which contains all load and save logic.
        """
        self._sl.load()

    def finalize(self, save):
        """ finalize experiment

        This method should be called befor experiment exit. 

        """
        if save:
            self._sl.update_struct()
            path = self._sl.pack()
            self._sl.clear_temp()
            return path
        self._sl.clear_temp()

    def generate_trial(self, run):
        """ generates trial

        This method generates a trial useing the parameter set with its specific
        values given by the current run.        
        
        Parameters
        ----------
        run : :class:`Run`
            Reference on the Run, the next Trial is needed for.
        
        Returns
        -------
        trial : :class:`Trial`
            new Trial object with all parameters and variable values are set
            correctly
        """
        trial = Trial(run.variable,run._parameters,run.reference_signal,
                      run.pre_signal, run.between_signal, run.post_signal,
                      run.sample_rate, run.calib, None)
        return trial

    def time_to_signal(self, obj):
        """ convert given time to zero signal

        This function checks if for a given object a signal is specified
        as float or tuple and converts it into a zero signal of given length.

        Parameters
        ----------
        obj : :class:`Run``, :class:`Trial` or subtype of :class:`Experiment`
            The Experiment, Run or Trial to check signals
        """
        signals = ['reference_signal','test_signal', 'pre_signal', 'post_signal',
                   'between_signal']
        for signal in signals:
            sig = getattr(obj,signal)
            if isinstance(sig,tuple):
                if len(sig) == 1:
                    setattr(obj,signal,np.zeros(sig[0]*obj.sample_rate))
                else:
                    setattr(obj,signal, np.zeros((sig[0]*obj.sample_rate, sig[1])))
            elif isinstance(sig, int) or isinstance(sig, float):
                setattr(obj,signal, np.zeros(sig*obj.sample_rate))

    def next_trial(self, run):
        """bulid next trial
               
        Parameters
        ----------
        run : :class:`Run`
       
        Returns
        -------
        trial : :class:`Trial`
        
        signal : list of numpy arrays
        
        """
        trial = self.generate_trial(run)
        trial.correct_answer = self.correct_answer()
        self.init_trial(trial)
        self.time_to_signal(trial)
        signal = self.build_signal(trial)
        return trial, signal

    def skip_run(self, run):
        """ sets skipped to True
        """
        run.skipped = True

 
class AFCExperiment(Experiment):
    """This class provides basic functions for an N-AFC experiment using
    the methods :func:`generate_trial`, :func:`build_signal` and :func:`check_answer`.
    
    Attributes
    ----------
    num_afc : int
        number of intervals per trial
        :func:`build_signal` for further information
    """    
    num_afc = 3 #default
    task = "In which interval do you hear the test tone? "

    def correct_answer(self):
        """set correct answer for given trial

        depending on the current experiment type this method sets the right
        answer for each trial

        Returns
        -------
        correct_answer : string or int
            depending on eperiment type return correct answer      
        """
        
        return random.randint(1,self.num_afc)

    def build_signal(self, trial):
        """build signal for N-AFC experiment
        
        This method prepares a list of test stimulus and reference stimulus
        in an N-AFC manner.
        
        Parameters
        ----------
        trial : :class:`Trial`
        
        Returns
        -------
        signal : list of numpy array
            list containes pre-signal, post-signal, between signal, 
            N-1 reference stimuli and the test stimulus.
        """
        if type(trial.reference_signal) is list:
            if len(trial.reference_signal) == self.num_afc-1:
                random.shuffle(trial.reference_signal)
                trial.reference_signal = iter(trial.reference_signal)
            else:
                raise ValueError("""Number of reference intervals does not match
                number of experiment reference intervals""")
        signal = []
        signal.append(trial.pre_signal)
        for x in range(self.num_afc):
            if x == trial.correct_answer-1: # TEST
                signal.append(trial.test_signal)
            else:
                if hasattr(trial.reference_signal, '__next__'):
                    next_ref = trial.reference_signal.__next__()
                    signal.append(next_ref)
                else:
                    signal.append(trial.reference_signal)
            if x != self.num_afc - 1: # BETWEEN (quiet)
                signal.append(trial.between_signal)
        signal.append(trial.post_signal)
        return signal

    def check_answer(self,answer):
        """check answer formate
        
        This method checks if the answer is able to be an integer and if its 
        inside the range of possible results of the N-AFC experiment.
        
        Parameters
        ----------
        answer : string
            The given answer as tring
        
        Returns
        -------
        answer : int
           if answer type is correct it returns the answer as int

        Raises
        ------
        WrongAnswerFormat
        
        """
        try: # Check for whole number
            answer = int(answer)
        except ValueError:
            raise expt.WrongAnswerFormat("Please Enter a whole number")
        if (answer < 1 or 
            answer > self.num_afc): # Check if answer is in intervall
            raise expt.WrongAnswerFormat("Please enter a number between 1 and %d" %
                                         self.num_afc)
        return answer


class MatchingExperiment(Experiment):
    """This class provides basic functions for an matching experiment using
    the methods :func:`generate_trial`, :func:`build_signal` and :func:`check_answer`.
    
    
    Attributes
    ----------
    ref_position : int
        Depending on ref_position the referenc signal is 
        (0) set randomly,
        (1) the first one, or
        (2) the second one.
    """
    ref_position = 1 #default
    
    def correct_answer(self):
        """set correct answer for given trial

        depending on the current experiment type this method sets the right
        answer for each trial

        Returns
        --------
        correct_answer : string or int
            depending on eperiment type return correct answer      
        """
        return 'd'
        

    def build_signal(self,trial):
        """build signal for matching experiment
        
        This method prepares a list of test stimulus and reference stimulus.
        :class:`MatchingExperiment` for further information.      
                 
        Parameters
        ----------
        trial : :class:`Trial`
        
        Returns
        -------
        signal : list of numpy array
            list containes pre-signal, post-signal, between signal, 
            reference stimuli and the test stimulus.
        """
        signal = []
        signal.append(trial.pre_signal)
        if self.ref_position == 0:
            signals = [trial.test_signal, trial.reference_signal]
            random.shuffle(signals)
            signal = signal + signals[0] + trial.between_signal + signals[1]
        elif self.ref_position == 1:
            signal = signal + [trial.reference_signal] + [trial.between_signal] + [trial.test_signal]
        elif self.ref_position == 2:
            signal= signal + trial.test_signal + trial.between_signal + trial.reference_signal
        signal.append(trial.post_signal)
        return signal

    def check_answer(self, answer):
        """check answer format
        
        This method checks if the answer is up or down.
        Nothing else is excepted.  
        
        Parameters
        ----------
        answer : string
        
        Returns
        -------
        answer : string
        """
        if answer == "d" or answer == "u":
            return answer
        else:
            raise expt.WrongAnswerFormat("Only answer 'u' and 'd' are allowed")
            


        
