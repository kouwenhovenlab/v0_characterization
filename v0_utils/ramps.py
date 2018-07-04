import numpy as np
from qcodes.utils.validators import Numbers

from .qcodes_tools import VirtualInstrument


class StaircaseRamp(VirtualInstrument):
    """
    Encapsulates parameters of a staircase ramp of a parameter, assumes volts
    as the unit.

    Args:
        name
            Name of the staircase ramp instrument, useful for referring to in
            snapshot
    """

    def __init__(self,
                 name: str,
                 **kwargs):
        super().__init__(name, **kwargs)

        # Generic sweep definition parameters
        self.add_parameter(name='start_ramp_voltage',
                           label='Voltage at the ramp beginning',
                           unit='V',
                           get_cmd=None,
                           set_cmd=None,
                           get_parser=float,
                           initial_value=0,
                           vals=Numbers(),
                           docstring="actually, its a.u. but, if later, "
                                     "the AWG channel amplitude is set to 1V, "
                                     "then this a.u. also become V)"
                           )
        self.add_parameter(name='finish_ramp_voltage',
                           label='Voltage at the ramp end',
                           unit='V',
                           get_cmd=None,
                           set_cmd=None,
                           get_parser=float,
                           initial_value=0,
                           vals=Numbers(),
                           docstring="actually, its a.u. but, if later, "
                                     "the AWG channel amplitude is set to 1V, "
                                     "then this a.u. also become V)"
                           )
        self.add_parameter(name='n_steps',
                           label='Number of steps in staircase ramp',
                           unit='#',
                           get_cmd=None,
                           set_cmd=None,
                           get_parser=int,
                           initial_value=1,
                           vals=Numbers(min_value=1),
                           docstring="Number of steps inside the staircase ramp"
                           )

        # Parameter to be used in measurement
        self.add_parameter(name='values_vector',
                           label='Voltage',
                           unit='V',
                           get_cmd=self._get_staircase_values_vector,
                           set_cmd=False,
                           snapshot_value=False,
                           vals=Numbers(),
                           docstring="Vector of values that the staircase "
                                     "ramp contains. This parameter can be "
                                     "referred to in Measurement."
                           )

    def _get_staircase_values_vector(self):
        return np.linspace(
            self.start_ramp_voltage(),
            self.finish_ramp_voltage(),
            self.n_steps()
        )


class RepeatingStaircaseRamp(StaircaseRamp):
    """
    Encapsulates parameters of a repeating staircase
    """

    def __init__(self,
                 name: str,
                 **kwargs):
        super().__init__(name, **kwargs)

        self.add_parameter(name='n_repetitions',
                           label='Number of ramp repetitions',
                           unit='#',
                           get_cmd=None,
                           set_cmd=None,
                           get_parser=int,
                           initial_value=1,
                           vals=Numbers(min_value=1),
                           docstring="the number of time the fast staircase "
                                     "is going to be repeated this is useful "
                                     "for averaging the results and getting "
                                     "better accuracy"
                           )

        # Convenient get-only parameters
        self.add_parameter(name='n_all_steps',
                           label='Total number of steps',
                           unit='#',
                           get_cmd=self._get_n_all_steps,
                           set_cmd=False,
                           snapshot_value=False,
                           get_parser=int,
                           vals=Numbers(),
                           docstring="Total number of steps summed up "
                                     "for all staircases within the "
                                     "sequence"
                           )

        # Parameter to be used in measurement
        self.add_parameter(name='values_with_repetitions_vector',
                           label='Voltage',
                           unit='V',
                           get_cmd=self._get_values_with_repetitions_vector,
                           set_cmd=False,
                           snapshot_value=False,
                           vals=Numbers(),
                           docstring="Vector of values that the all "
                                     "the repeated staircase ramps ramp "
                                     "contain. This parameter can be "
                                     "referred to in Measurement."
                           )
        self.add_parameter(name='all_repetitions_vector',
                           label='Vector of repetition indices',
                           unit='',
                           get_cmd=self._get_all_repetitions_vector,
                           set_cmd=False,
                           snapshot_value=False,
                           vals=Numbers(),
                           docstring="Vector of indices of repetitions for "
                                     "each point in the repeated staircase "
                                     "ramp. This parameter can be referred to "
                                     "in Measurement."
                           )

    def _get_values_with_repetitions_vector(self):
        values_with_repetitions_vector = \
            np.tile(self.values_vector(), self.n_repetitions())
        return values_with_repetitions_vector

    def _get_all_repetitions_vector(self):
        n_steps_grid, n_repetitions_grid = np.meshgrid(
            np.arange(0, self.n_steps(), 1),
            np.arange(0, self.n_repetitions(), 1),
            indexing='xy'
        )
        all_repetitions_vector = np.reshape(n_repetitions_grid, -1)
        return all_repetitions_vector

    def _get_n_all_steps(self):
        return self.n_repetitions() * self.n_steps()
