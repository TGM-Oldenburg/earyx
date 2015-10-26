from earyx.experiments import AFCExperiment
from earyx.order import Sequential
from earyx.utils import gensin, rms
import numpy as np
import earyx

class SineInNoise(AFCExperiment, Sequential):

    def init_experiment(self, exp):
        exp.add_parameter("noise_level", [-40, -60], 'dB')
        exp.set_variable("sine_level", -20, 'dB')
        exp.add_adapt_setting('1up2down', max_reversals = 8,
                              start_step = 5, min_step = 1)

        exp.num_afc = 3
        exp.discard_unfinished_runs = False
        exp.pre_signal = 0.3
        exp.between_signal = 0.3
        exp.post_signal = 0.2

        exp.description = """This is the description
        of the experiment"""

    def init_run(self, run):
        ref = np.random.randn(np.round(0.3*run.sample_rate))
        ref = ref/rms(ref)*10**(run.noise_level/20)
        run.reference_signal = ref

    def init_trial(self, trial):
        ampl = np.sqrt(2)*10**(trial.variable/20)
        test = gensin(1600, ampl, 0.03, trial.sample_rate)
        pos = np.round((len(trial.reference_signal) - len(test))/2)
        trial.test_signal = trial.reference_signal.copy()
        trial.test_signal[pos:pos+len(test)] += test

if __name__ == '__main__':
    earyx.start(SineInNoise)
