from qcodes import Instrument

class HardwareSweep(Instrument):
    def run(self):
        raise NotImplementedError("Subclasses of HardwareSweep should "
                                  "implement run method")
