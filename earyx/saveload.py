"""This module contains a class for saving an loading earyx experiments.

It is part of the earyx toolbox for psychoacoustic experiments. 
"""
from earyx.run import Run
from earyx.trial import Trial
import soundfile as sf
import json
import zipfile
import hashlib
import os
import datetime
import tempfile
import shutil
import tkinter as tk
from tkinter import filedialog
import statistics


class SaveLoad():
    """This class provides functions to save or load earyx experiments using
    the methods :func:`dump` and :func:`load`. A Zip file is created
    containing all signals of the experiment as wav files.  The structural state
    is saved as json file.

    Attributes
    ----------
    signal_names : list of str
        List of all signal names occur in experiments.
    _save_names : list of str
        List of all hash names of the signals.
    file_name : str
        path and name of zip file to save to or load from.
    files : dict
        Dictonary containing all loaded signals as numpy arrays with their hash
        name as keys
    experiment : Experiment-like object
        reference to the experiment to save
    """

    
    def __init__(self, experiment):
        """initialization of the object

        Parameters
        ----------
        experiment : experiment-like object
            reference to experiment to save
        """
        
        self.signal_names = ["pre_signal", "reference_signal", "between_signal",
                             "test_signal", "post_signal"]
        self._save_names = []
        self.signals = {}
        self.experiment = experiment
        self.zip_path = None
        self.temp_path = tempfile.mkdtemp(prefix='tmp_', dir=os.getcwd())
        
    def unify_signals(self, obj):
        for signal_name in self.signal_names:
            if signal_name in obj._save_names:
                continue
            signal = getattr(obj, signal_name)
            if signal != []:
                name = hashlib.md5(signal).hexdigest()
                if name in self.signals:
                    setattr(obj, signal_name, self.signals[name])
                    # signal = self.signals[name]
                else:
                    self.signals.update({name:signal})
                    #signal = self.signals[name]
                    setattr(obj, signal_name, self.signals[name])
                    sf.write(os.path.join(self.temp_path, name+'.wav'),
                             self.signals[name],
                             samplerate = obj.sample_rate)
                obj._save_names[signal_name] = name

    def update_struct(self):
        sct = json.dumps(self.experiment, sort_keys=True, indent=4,
                         default=self.to_json)
        with open(os.path.join(self.temp_path, 'struct.txt'), 'w') as f:
            f.write(sct)



    def to_json(self, python_object):
        """default function for json dump

        This method handles object serialization of the given custom object
        `python_object`. Supported is serialization of the whole experiment, its
        runs and trials. During this process signals are saved in the zip file.

        Parameters
        ----------
        python_object : Experiment, Run or Trial
            The python object to serialize. It can be a subtype of
            :class:`Experiment`, subtype of :class:`Run` or :class:`Trial`.

        Returns
        -------
        dct : dict
            Dictonary containing the structural data of given object and
            references to the saved signals

        Raises
        ------
        TypeError
            TypeError is raised for object types other than specified
        """
        if isinstance(python_object, type(self.experiment)):
            dct = self._create_dict(python_object)
            del dct['signals']
            del dct['_sl']
            return dct
        if issubclass(type(python_object), Run):
            dct = self._create_dict(python_object)
            if self.experiment.discard_unfinished_runs:
                dct['step'] = dct['start_step']
                dct['variable'] = self.experiment.variable['start_val']
                dct['trials'] = []
            del dct['_parameters']
            return dct
        if isinstance(python_object, Trial):
            return self._create_dict(python_object)
        raise TypeError(repr(python_object) + ' is not JSON serializable')

    
    def _create_dict(self, python_object):
        """Helper method to create save dict of given object.

        if signals of object not saved yet they will be using
        :function:`_save_signals_in_struct`. Original numpy array signals are
        removed from dictonary for json compatibility.

        Parameters
        ----------
        python_object : Experiment, Run or Trial
            See :function:`to_json` for further information

        Returns
        -------
        dct : dictonary
            Dictonary containing the structural data of given object and
            references to the saved signals
        """
        dct = python_object.__dict__.copy()
        del dct["reference_signal"]
        del dct["test_signal"]
        del dct["pre_signal"]
        del dct["post_signal"]
        del dct["between_signal"]
        return dct


    def pack(self):
        """Dump experiment in actual state to zip file.

        This method is the entry point for saving experiments. It takes the
        whole experiment and creates the zip file containing structure and data
        of the experiment.

        Parameters
        ----------
        zip_file : str
            Path to the zip file
        """
        self.psylab_export()
        if not self.zip_path:
            self.zip_path = "%s_%s_%s.zip" % (self.experiment.cls,
                                              self.experiment._create_time,
                                              self.experiment.subject_name)
        with zipfile.ZipFile(self.zip_path, 'w') as myzip:
            for root, dirs, files in os.walk(self.temp_path):
                for file in files:
                    myzip.write(os.path.join(root,file), arcname=file)
        return self.zip_path



    def clear_temp(self):
        shutil.rmtree(self.temp_path)
        
    def load(self):
        """ loads experiment from zip file and restore saved state

        This method loads an experiment from a zip file an restore its state.
        If the experiment does not match the experiment saved to zip file an
        error occurs.
        """

        self._save_names = []
        self.signals = {}

        root = tk.Tk()
        root.withdraw()
        options = {}
        options['defaultextension'] = '.zip'
        options['filetypes'] = [('zip files', '.zip')]
        options['initialdir'] = os.getcwd()
        options['parent'] = root
        options['title'] = 'Choose zip file to load'
        zip_path = filedialog.askopenfilename(**options)
        
        if not os.path.isfile(zip_path):
            raise FileExistsError()
        self.zip_path = zip_path
        if os.path.isdir(self.temp_path):
            shutil.rmtree(self.temp_path)
        self.temp_path = tempfile.mkdtemp(prefix='tmp_',
                                          dir=os.path.dirname(zip_path))

        with zipfile.ZipFile(self.zip_path) as myzip:
            myzip.extract('struct.txt', self.temp_path)
            with myzip.open("struct.txt") as myfile:
                sct = json.loads(myfile.read().decode())
            for name in myzip.namelist():
                if name[-4:] == ".wav":
                    myzip.extract(name, self.temp_path)
                    self._save_names.append(name[:-4])
                    self.signals[name[:-4]] = sf.read(os.path.join(self.temp_path,name),
                                                      always_2d = False)[0]

        for idx, run in enumerate(self.experiment.runs):
            for trial in sct["runs"][idx]["trials"]:
                trial_obj = Trial.create_trial()
                trial_obj.__dict__.update(trial)
                self.separate_signals(trial_obj)
                run.trials.append(trial_obj)
            del sct["runs"][idx]["trials"]
            run.__dict__.update(sct["runs"][idx])
            self.separate_signals(run)
        del sct["runs"]
        self.experiment.__dict__.update(sct)
        self.separate_signals(self.experiment)
        print('Successfully loaded experiment')


    def separate_signals(self, obj):
        """ loads signals from save dictonary and restore state in object

        This method iterates through the signals in save struct. If signal is
        present it is inserted into the corresponding object

        Parameters
        ----------
        obj : :class:`Run`, :class:`Trial`, or :class:`Experiment`
            obj is one of this three stages in experiment structure
            in which the signal can occur
        """
        for signal_name in self.signal_names:
            if signal_name in obj._save_names:
                if isinstance(obj._save_names[signal_name], list):
                    signal_temp = [sig for sig in
                                   self.signals[obj._save_names[signal_name]]]
                    setattr(obj, signal_name,  signal_temp)
                else:
                    setattr(obj, signal_name, self.signals[obj._save_names[signal_name]])
                    # signal = self.signals[obj._save_names[signal_name]]

    def psylab_export(self):
        
        runs = [run for run in self.experiment.runs if run.finished]
        if runs:
            name = self.experiment.subject_name.replace(" ", "")
            with open(os.path.join(self.temp_path, 'psydat_'+name), 'w') as f:
                f.write('######## psydat version 2 header ########  DO NOT change THIS line ########\n')
                for run in runs:
                    f.write('#### %s %s %s npar %d ####\n' % (self.experiment.cls,
                                                              self.experiment.subject_name,
                                                              run.finished,
                                                              len(self.experiment.parameters)))
                    idx = 1
                    for par, items in self.experiment.parameters.items():
                        f.write('%%----- ')
                        f.write('PAR%d: %s %d %s\n' % (idx, par,
                                                             getattr(run,par),
                                                             items['unit']))
                        f.write('%%----- VAL:')
                        for trial in run.trials:
                            f.write(' %d %d' % (trial.variable, trial.is_correct))
                        f.write('\n')

                        measure = [val.variable for val in run.trials[run.start_measurement_idx:]]
                        med = statistics.median(measure)
                        std = statistics.stdev(measure)
                        maxi = max(measure)
                        mini = min(measure)
                        f.write('  %s %d %d %d %d %s\n' % (self.experiment.variable['name'],
                                                          med, std, maxi, mini,
                                                          self.experiment.variable['unit']))
                        idx = idx+1
                        
            


            
        
