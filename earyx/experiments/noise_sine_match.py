from earyx.experiments import MatchingExperiment
from earyx.order import Sequential
from earyx.utils import gensin, rms, fft_rect_filt, hanwin
import numpy as np
import earyx

class NoiseSineMatch(MatchingExperiment, Sequential):

    def init_experiment(self, exp):
        exp.add_parameter("frequency",[100, 200, 500, 1000, 2000, 4000], "Hz")
        exp.set_variable("gain", -30, "dB")
        exp.add_adapt_setting("1up2down", 3, 8, 1)
        exp.task = "loudness of the noise should go (u)p/(d)own? "
        exp.debug = False
        exp.discard_unfinished_runs = False
        exp.description = """This is the description of matching experiment"""

        ref = gensin(1000, 1, 0.6, 0, exp.sample_rate)
        srms = rms(ref)
        exp.reference_signal = ref/srms*10**(-30/20)
        exp.reference_signal = hanwin(exp.reference_signal, 0.05)
        exp.pre_signal = 0.1
        exp.between_signal = 0.2
        exp.post_signal = 0.3

    def init_run(self, cur_run):
        """Set signals for reference and pauses between them."""

        cur_run.variable = np.random.randint((-30-10), (-30+10))
        return cur_run

    def init_trial(self, trial):
        """Set signal for variable."""
        trial.test_signal = np.random.randn(0.6*trial.sample_rate)
        trial.test_signal = fft_rect_filt(trial.test_signal,
                                          trial.frequency-50,
                                          trial.frequency+50,
                                          trial.sample_rate)
        
        trial.test_signal = trial.test_signal/rms(trial.test_signal)*10**(trial.variable/20)
        trial.test_signal = hanwin(trial.test_signal, 0.05)
        return trial

if __name__ == '__main__':
    earyx.start(NoiseSineMatch)
