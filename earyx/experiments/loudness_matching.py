# -*- coding: utf-8 -*-
"""
Created on Fri May  8 12:07:46 2015

a little loudness matching experiment

@author: Sh3rmann
"""
from earyx.experiments import MatchingExperiment
from earyx.order import Sequential
from earyx.utils import gensin
import numpy as np
import earyx.ui as UI
import earyx

class LoudnessMatching(MatchingExperiment, Sequential):

    def init_experiment(self, exp):
        """Set all parameters for one's own experiment."""
        exp.add_parameter("frequency",[500, 1500, 3000], "Hz")
        exp.set_variable("gain", -15, "dB")
        exp.add_adapt_setting("1up2down", 3, 8, 1)
        exp.sample_rate = 48000
        exp.gain = 1.0
        exp.calib = 0
        exp.task = "The second tone needs to go (u)p/(d)own"
        exp.ui = "Tui"
        exp.debug = False
        exp.discard_unfinished_runs = False
        exp.allow_debug = True
        exp.feedback = True
        exp.description = """This is the description of matching experiment"""
        exp.visual_indicator = True

    def init_run(self, cur_run):
        """Set signals for reference and pauses between them."""
        print(self.parameters['frequency']['values'][0])
        ref = gensin(self.parameters['frequency']['values'][0],1,1,0,cur_run.sample_rate)
        rms = np.sqrt(np.mean(np.square(ref)))
        cur_run.reference_signal = ref/rms*10**(-30/20)
        cur_run.pre_signal = np.zeros(0.5*cur_run.sample_rate)
        cur_run.between_signal = cur_run.pre_signal
        cur_run.post_signal = cur_run.pre_signal
        return cur_run

    def init_trial(self, trial):
        """Set signal for variable."""
        gain = 2**0.5*10**(trial.variable/20)
        trial.test_signal = gensin(trial.frequency,gain,1,0,trial.sample_rate)
        return trial

if __name__ == '__main__':
    earyx.start(LoudnessMatching)
