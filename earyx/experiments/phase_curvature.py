from earyx.experiments import AFCExperiment
from earyx.order import Sequential
from earyx.utils import gensin, htc, hanwin
import numpy as np
import earyx

class PhaseCurvature(AFCExperiment, Sequential):
    def init_experiment(self, exp):

        self.add_parameter("C",  [-1.0],
                           "Val", "Desc")
        self.add_parameter("signal_freq", [ 500, 300, 1000],
                           "Hz", "next desc")
        self.set_variable("sine_level", 70, "dB", "level of the test signal")
        self.add_adapt_setting("1up2down", 8, 5, 2)
        self.sample_rate = 32000
        self.calib = 100
        self.num_afc = 3
        self.task = "In which Interval do you hear the test tone (1,2,3)?"
        self.discard_unfinished_runs = False
        self.debug = True
        self.feedback = True
        self.description = """ Description of phase curvature"""

        # signal generation
        pause_len = 0.05
        self.between_signal = np.zeros(np.round(
             pause_len*self.sample_rate))
        self.post_signal = self.between_signal[1:len(
            self.between_signal)/2]
        self.pre_signal = self.between_signal

    def init_run(self, cur_run):
        """Set signals for reference and pauses between them."""

        ramp_dur_htc = 0.05
        cur_run.reference_signal = htc(75, cur_run.sample_rate, 0.32,
                                      cur_run.signal_freq/10,
                                      0.4*cur_run.signal_freq,
                                      1.6*cur_run.signal_freq,
                                       cur_run.C, cur_run.calib)
        cur_run.reference_signal = hanwin(cur_run.reference_signal,
                                          np.round(ramp_dur_htc*
                                                   cur_run.sample_rate))

    def init_trial(self, trial):
        """Set signal for variable."""

        sine_dur = 0.26
        ramp_dur_sine = 0.03
        ampl = np.sqrt(2)*10**((trial.variable-trial.calib)/20)
        start_phase = np.random.randint(0, 361)
        test_tone = gensin(trial.signal_freq, ampl, sine_dur, start_phase,
                           trial.sample_rate)
        test_tone = hanwin(test_tone,
                           np.round(ramp_dur_sine*trial.sample_rate))
        trial.test_signal = trial.reference_signal.copy()
        start_sample = np.round((len(trial.reference_signal)-len(test_tone))/2)
        trial.test_signal[start_sample:start_sample+len(test_tone)] += test_tone

if __name__ == '__main__':
    earyx.start(PhaseCurvature)
