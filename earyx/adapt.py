import earyx.exception as exp


class Adapt():
    def __init__(self, parameters):
        self.__dict__.update(parameters)
        self.init_adapt()

    def init_adapt(self):
        pass

    def adapt(self, trials):
        pass

    def __call__(self, trials):
        return self.adapt(trials)


class Adapt1up2down(Adapt):
    reversals = -1

    def adapt(self, trials):
        """
        Set new value of reversal variable self.reversals and stepsize
        variable self.step according to the adaptive 1up-2down paradigm.
        (Levitt, "Transformed up-down procedures in psychoacoustics",
        1971, JASA 49, p.467-477.)

        Parameters
        ----------
        trials : List with all trials

        Returns
        -------
        result : (none)
        Updated self.step and self.reversals
        """
        if len(trials) >= 3:
            if (all([trials[-1].is_correct, trials[-2].is_correct]) and
                not trials[-3].is_correct):
                if self.minstep == self.step:
                    self.reversals += 1
                self.step = max(self.minstep, self.step/2)

            if (not trials[-1].is_correct and
                all([trials[-2].is_correct, trials[-3].is_correct])):
                if self.minstep == self.step:
                    self.reversals += 1

            # check for end of run
            if self.reversals == self.max_reversals:
                raise exp.RunFinishedException()
        if not trials[-1].is_correct:
            return self.step
        if (len(trials) >= 2 and
            trials[-2].is_correct):
            return -self.step
        return 0


class Adapt2up1down(Adapt):

    reversals = -1

    def adapt(self, trials):
        """
        Set new value of reversal variable self.reversals and stepsize
        variable self.step according to the adaptive 2up-1down paradigm.
        (Levitt, "Transformed up-down procedures in psychoacoustics",
        1971, JASA 49, p.467-477.)

        Parameters
        ----------
        trials : list (of trials)
            List with all trials
        
        Returns
        -------
        result : 
            Updated self.step and self.reversals

        Raises
        ------
        RunFinishException
        """
        if len(trials) >= 3:
            if (not all([trials[-2].is_correct, trials[-3].is_correct]) and
                trials[-1].is_correct is True):
                if self.minstep == self.step:
                    self.reversals += 1
                self.step = max(self.minstep, self.step/2)

            if (trials[-3].is_correct is True and
                not all([trials[-1].is_correct, trials[-2].is_correct])):
                if self.minstep == self.step:
                    self.reversals += 1

            # check for end of run
            if self.reversals == self.max_reversals:
                raise exp.RunFinishedException()

        if trials[-1].is_correct is True:
            return -self.step
        if (len(trials) >= 2 and
            trials[-2].is_correct is False):
            return self.step
        return 0


class Adapt1up3down(Adapt):

    reversals = -1

    def adapt(self, trials):
        """
        Set new value of reversal variable self.reversals and stepsize
        variable self.step according to the adaptive 3up-1down paradigm.
        (Levitt, "Transformed up-down procedures in psychoacoustics",
        1971, JASA 49, p.467-477.)

        Parameters
        ----------
        trials : List with all trials

        Returns
        -------
        result : (none)
        Updated self.step and self.reversals
        """
        if len(trials) >= 4:
            if (all([trials[-1].is_correct,
                     trials[-2].is_correct,
                     trials[-3].is_correct]) and
                not trials[-4].is_correct):
                if self.minstep == self.step:
                    self.reversals += 1
                    self.step = max(self.minstep, self.step/2)

            if (not trials[-1].is_correct and
                all([trials[-2].is_correct,
                     trials[-3].is_correct,
                     trials[-4].is_correct])):
                if self.minstep == self.step:
                    self.reversals += 1

            # check for end of run
            if self.reversals == self.max_reversals:
                raise exp.RunFinishedException()

        if trials[-1].is_correct is False:
            return self.step
        if (len(trials) >= 3 and
            trials[-2].is_correct is True and
            trials[-3].is_correct is True):
            return -self.step
        return 0


class AdaptWUD(Adapt):

    reversals = -1

    def adapt(self, trials):
        """
        Set new value of reversal variable self.reversals and stepsize
        variable self.step according to the "weighted up-down" paradigm.
        (Kaernbach, "Simple adaptive testing with the weighted up-down
        method", 1991, Perception & Psychophysics, 49, p. 227-229)

        Parameters
        ----------
        trials : List with all trials

        Returns
        -------
        result : (none)
        Updated self.step and self.reversals
        """
        if len(trials) >= 2:
            if (trials[-1].is_correct and not trials[-2].is_correct):
                if self.minstep == self.step:
                    self.reversals += 1
                    self.step = max(self.minstep, self.step/2)

            if (not trials[-1].is_correct and trials[-2].is_correct):
                if self.minstep == self.step:
                    self.reversals += 1
            # check for end of run
            if self.reversals == self.max_reversals:
                raise exp.RunFinishedException()

        if self.pc_convergence >= 1:
            return  # error above 100 %

        step_down = self.start_step
        step_up = self.pc_convergence/(1-self.pc_convergence)*step_down

        if trials[-1].is_correct is False:
            return step_up
        else:
            return -step_down
