import testui
from earyx.experiments import AFCExperiment
from earyx.order import Sequential
from earyx.utils import gensin
import numpy as np
import earyx.ui



class testexperiment(AFCExperiment, Sequential):
    def init_experiment(self):

        self.add_parameter("frequency",[1000,2000,3000],"Hz","Desc")
        self.set_variable("sine_level", -20, "dB","Desc")
        self.add_adapt_setting("1up2down",6,8,1)
        
       # self.ui = testui.Testui
        
        self.debug = False
        self.num_afc = 3
        self.sample_rate = 48000
        self.calib = 0
        self.task = "In which Interval do you hear the test tone (1,2,3)?"

    def init_run(self, cur_run):
        """Set signals for reference and pauses between them."""
        cur_run.reference_signal = np.array([0.4])
        cur_run.pre_signal = np.array([0.0])
        cur_run.between_signal = np.array([.2])
        cur_run.post_signal = np.array([.9])

    def init_trial(self, cur_trial):
        """Set signal for variable."""
        cur_trial.test_signal = np.array([0.8])

def test_exp():
    t = testexperiment()
    testui.Testui(t)
   













