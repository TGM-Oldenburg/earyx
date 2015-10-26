class Trial():
    """This class sets all parameters, generates the signals defined by the user in
       the actual experiment's script and plays it back.
       
    Attributes
    ----------
    reference_signal : numpy array
    pre_signal : numpy array
        pre_signal
    between_signal : numpy array
        between signal
    post_signal : mumpy array
        post signal
    test_signal : list
    correct_answer : str or int
    sample_rate : int
    calib : float
    answer : boolean
    is_correct : boolean
    variable : dict
        needs to contain name (string), value, unit (string)
    parameters : dict
        containing name, value, unit and description.
    signal : list
    _save_names : dict    
    """
    def __init__(self, variable, parameters, reference_signal, pre_signal,
                 between_signal, post_signal, sample_rate, calib, correct_answer):
        """initialization.

        Parameters
        ---------- 
        variable : dict
            needs to contain name (string), value, unit (string)
        parameters : dict
            containing name, value, unit and description.
        reference_signal : numpy array
        pre_signal : numpy array
        between_signal : numpy array
        post signal : numpy array
        sample_rate : int
        calib : float
        correct_answer : str or int
        """
        self.reference_signal = reference_signal
        self.pre_signal = pre_signal
        self.between_signal = between_signal
        self.post_signal = post_signal
        self.test_signal = []
        self.correct_answer = correct_answer
        self.sample_rate = sample_rate
        self.calib = calib
        self.answer = None
        self.is_correct = False
        self.variable = variable
        self.__dict__.update(parameters)
        self.signal = []
        self._save_names = {}

    @classmethod
    def create_trial(cls):
        """ create empty tiral to load data
        
        Parameters
        ----------
        cls : Class
            should be Trial
            
        Returns
        -------        
        cls : Class
            :class:`Trial`
        """
        return cls(0, {}, [], [], [], [], 0, 0, 0)
