"""
This module contains als Run related classes and mathods. Until now there is
only one class :class:`Run` describing the basic functionality of a earyx Run.

"""

class Run():
    """This class contains all parameters, a list of trials and settings for a single run.     
    
    Attributes
    ----------
    variable : dict
        needs to contain name (string), value, unit (string)
    adapt_settings : dict
    parameters : dict
        containing name, value, unit and description.
    sample_rate : int
    calib : float
    finished : boolean
        if run is finished
    trials : list
        list of trials :class:`Trial`
    test_signal : list 
    reference_signal : mumpy array 
        reference signal
    between_signal : numpy array
        signal between reference and test or test and test signal
    post_signal : numpy array
        post signal
    pre_signal : numpy array
        pre signal
    step : int
        step (later changed by adapt methods)
    _save_names : dict
    skipped : boolean
    start_measurement_idx : int
    """
    def __init__(self, parameters, variable, adapt_settings,
                 reference_signal, pre_signal, between_signal, post_signal,
                 sample_rate, calib):
        """initialization.

        Parameters
        ----------    
        parameters : dict
            containing name, value, unit and description.
        variable : dict
            needs to contain name (string), value, unit (string)
        adapt_settings : dict    
        reference_signal : mumpy array 
            reference signal
        pre_signal : numpy array
            pre signal
        between_signal : numpy array
            signal between reference and test or test and test signal
        post_signal : numpy array
            post signal
        test_signal : numpy array
        sample_rate : int
        calib : float
        """
        self.variable = variable
        self.__dict__.update(adapt_settings)
        self._parameters = parameters
        self.__dict__.update(parameters)
        self.sample_rate = sample_rate
        self.calib = calib
        self.finished = False
        self.trials = []
        self.test_signal = []
        self.reference_signal = reference_signal
        self.between_signal = between_signal
        self.post_signal = post_signal
        self.pre_signal = pre_signal
        self.step = self.start_step
        self._save_names = {}
        self.skipped = False
        self.start_measurement_idx = None
        

    def get_param_string(self, params):
        """returns string containing all parameter information
               
        Parameters
        ----------
        params : dict
            containing name, value, unit and description
        
        Returns
        -------
        string : string
        """
        string = 'Parameters: '
        for param, value in self._parameters.items():
            string+= "%s: %d %s, " % (param, value, params[param]['unit'])
        return string[:-2]
            

