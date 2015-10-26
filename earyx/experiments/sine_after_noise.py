from earyx.experiments import AFCExperiment
from earyx.order import Sequential
from earyx.utils import gensin, fft_rect_filt, hanwin, rms
import numpy as np
import earyx.ui as UI
import earyx

class SineAfterNoise(AFCExperiment,Sequential):

    def init_experiment(self, exp):
        """Set all parameters for one's own experiment."""
        exp.add_parameter("noise_level",[-20, -47, -39, -31, -23, -18], "dB")
        exp.set_variable("sine_level", -20, "dB")
        exp.add_adapt_setting("1up2down",6,8,1)

        exp.num_afc = 3
        exp.sample_rate = 48000
        exp.calib = 0
        exp.task = "In which Interval do you hear the test tone? (1,2,3)"
        exp.debug = False
        exp.discard_unfinished_runs = False
        exp.feedback = True
        exp.description = """This is the description of the experiment"""


    def init_run(self, cur_run):
        """Set signals for reference and pauses between them."""
        pauselen = 0.3  # quiet signals
        cur_run.between_signal = np.zeros(np.round(
            pauselen*cur_run.sample_rate))  # m_quiet
        cur_run.post_signal = cur_run.between_signal[
            0:len(cur_run.between_signal)/2]  # m_postsig
        cur_run.pre_signal = cur_run.between_signal  # m_presig
        
    def init_trial(self, trial):
        """Set signal for variable."""

        noise_dur = 0.3         # duration of noise
        pause_dur = 0.03        # pause between noise and sine
        sine_dur = 0.015        # duration of test signal
        ramp_dur = 0.0075       # ramp of hann window

        sine_freq = 1600        # freq of test signal
        noise_freq = 1600       # midfreq of noise
        noise_band_width = 300  # bandwidth of noise

        # trial.test_signal = test_tone (matlab)
        sine_ampl = np.sqrt(2)*10**(trial.variable/20)
        m_test = gensin(sine_freq, sine_ampl, sine_dur, 0,
                                   trial.sample_rate)
        m_test = hanwin(m_test, np.round(
            ramp_dur*trial.sample_rate))

        # generate new instance of running noise
        m_ref = np.random.randn(np.round(noise_dur*trial.sample_rate))
        m_ref = fft_rect_filt(m_ref, noise_freq-noise_band_width/2,
                              noise_freq+noise_band_width/2, trial.sample_rate)

        # adjust its level
        m_ref = m_ref/rms(m_ref)*10**(trial.noise_level/20)
        # apply onset/offset ramps
        m_ref = hanwin(m_ref, np.round(ramp_dur*trial.sample_rate))


        pause_zeros = np.zeros(np.round(pause_dur*trial.sample_rate))
        sine_zeros = np.zeros(np.round(sine_dur*trial.sample_rate))
        trial.reference_signal = np.concatenate((m_ref, pause_zeros, sine_zeros))
        trial.test_signal = np.concatenate((m_ref, pause_zeros, m_test))



if __name__ == "__main__":
    earyx.start(SineAfterNoise)

    

