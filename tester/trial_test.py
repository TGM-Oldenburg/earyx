import sys
#sys.path.append('../..')

import os

os.chdir("../..")

import earyx.run as run
from earyx.experiments import AFCExperiment
from earyx.order import Sequential




def test_trials():
    testall = TestTrials()
    testall.test_trial_param_change()


class TestTrials():

    def __init__(self):
        self.test_run = run.Run({"stimuli_frequency":
                                {"values": [2000], "unit:": "Hz",
                                 "desc": "next desc"}},
                                {"name": "testtone_level", "unit": "dB",
                                 "startval": -20, "desc": "value to test"},
                                {"type": "1up2down", "max_reversals": 8,
                                 "start_step": 8, "minstep": 1}, "ref", "pre",
                                "between", "post", 48000, 0)

        class TestExperiment(AFCExperiment, Sequential):
            pass

        self.testAfc = TestExperiment()
        self.first_trial = self.testAfc.generate_trial(self.test_run)
        self.first_trial.test_signal = "testSignal"

        self.first_signal = self.testAfc.build_signal(self.first_trial)

        self._test_trial_options(self.first_signal)

    def _test_trial_options(self, signal):
        assert signal[0] == "pre"
        assert signal[2] == "between"
        assert signal[-1] == "post"

    # Test if signal position changes in different trials
    def test_trial_param_change(self):
        """
        Check if position of the signal differ in different trials.

        Function creates a reference trial and compares it which
        N (num_of_test_trials) other trials and check if the
        first position changed.
        """
        change_order = False
        num_of_test_trials = 10

        while not change_order:
            check_trial = self.testAfc.generate_trial(self.test_run)
            check_trial.test_signal = "testSignal"
            check_signal = self.testAfc.build_signal(check_trial)

            # check if positions from pre, between and post are correct
            self._test_trial_options(check_signal)

            num_of_test_trials -= 1
            if check_signal[1] != self.first_signal[1]:
                change_order = True
            elif num_of_test_trials == 0:
                assert 0 == 1, "no different signals found, pls check"
                change_order = True
