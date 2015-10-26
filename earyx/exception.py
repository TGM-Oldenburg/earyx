# Exception classes
class RunAbortException(Exception):
    def __init__(self, arg=""):
        # Set some exception infomation
        self.msg = arg

class RunFinishedException(Exception):
    def __init__(self, arg=""):
        self.msg = arg

class WrongAnswerFormat(Exception):
    def __init__(self, arg=""):
        self.msg = arg

class ExperimentAbortException(Exception):
    def __init__(self, arg=""):
        self.msg = arg

class ToggleDebugException(Exception):
    def __init__(self, arg=""):
        self.msg = arg

class RunStartMeasurement(Exception):
    def __init__(self, arg=""):
        self.msg = arg
