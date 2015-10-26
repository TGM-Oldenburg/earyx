import random

class Order():
    pass

class Sequential(Order):
    def next_run(self):
        for run in self.runs:
            if not (run.finished or run.skipped):
                return run
        raise StopIteration


                
class Interleaved(Order):

    def next_run(self):
        open_runs = list(filter(lambda run: (not (run.finished or run.skipped)),
                                self.runs))
        if open_runs:
            return random.choice(open_runs)
        raise StopIteration