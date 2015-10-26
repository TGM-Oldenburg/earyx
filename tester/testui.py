import earyx.ui
import earyx.exception as expt


class Testui(earyx.ui.Tui):
    
    def start(self, exp):
        exp.subject_name = "testui" #input("Pealse, type your name or Abbreveation: ")
        while True:
            try:
                run = exp.next_run()
            except StopIteration:
                self.message("Experiment finished")
                exp.finalize(True)
                return
            trial = exp.generate_trial(run)
            exp.init_trial(trial)
            signal = exp.build_signal(trial)
            self.present_signal(signal, trial.sample_rate)
            while trial.answer == None:
                try:
                    answer = self.get_user_response(exp.task)
                except expt.RunAbortException:
                    run.skip()
                    break
                except expt.ExperimentAbortException:
                    self.message("quit experiment")
                    self.finalize(True)
                    return
                except expt.ToggleDebugException:
                    exp.debug = not exp.debug
                    state = "on" if exp.debug else "off"
                    self.message("Debugging is '%s' now" % state)
                    continue
                try:
                    answer = exp.check_answer(answer)
                except expt.WrongAnswerFormat as e:
                    self.warning(e.msg)
                    continue
                else:
                    try:
                        exp.set_answer_and_adapt(run, trial, answer)
                    except expt.RunFinishedException:
                        if self.confirm("Run completed. Continue?"):
                            continue
                        else:
                            self.message("quit experiment")
                            return
                if exp.debug:
                    self.plot(run.trials)
                    
    def present_signal(self,signal, sample_rate):
        assert signal[0] == [.0]
        assert signal[6] == [.9] 
        
    def get_user_response(self, task):
        return 1
    
    def confirm(self, quest):
        return True
