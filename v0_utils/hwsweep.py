"""
THis module shall contain the infrastructure needed in order to implement
hardware sweeps.
"""

from qcodes import Instrument


class HardwareSweep(Instrument):
    """
    This is a base class for all the hardware sweeps.

    Subclasses shall add
    necessary parameters, and actual instruments (hardware) as modules. The
    `run` method shall contain the implementation of the measurement (i.e.
    interaction between the hardware instruments).

    Regarding representation of data captured by the hardware, one could
    choose just to return it from the `run` method, or to populate private
    object attributes which are linked to the get methods of corresponding
    parameters.

    Note: this is work-in-progress.
    """

    def run(self):
        raise NotImplementedError("Subclasses of HardwareSweep should "
                                  "implement run method")
