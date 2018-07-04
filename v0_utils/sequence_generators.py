import broadbean
import numpy as np
from broadbean.plotting import plotter as broadbean_plotter
from qcodes import Instrument
from qcodes.utils.validators import Numbers
from .ramps import RepeatingStaircaseRamp


class SequenceGenerator(Instrument):
    # __init__ should have all sequence-specific parameters
    def __init__(self,
                 name: str,
                 sequence_name: str=None,
                 **kwargs):
        super().__init__(name, **kwargs)

        self.sequence_name = sequence_name if sequence_name else name

    def make_broadbean_sequence(self) -> broadbean.Sequence:
        raise NotImplementedError("Subclasses of SequenceGenerator should "
                                  "implement make_broadbean_sequence method")

    def plot_broadbean_sequence(self):
        broadbean_plotter(self.make_broadbean_sequence())


class OneChannelOneMarkerGenerator(SequenceGenerator):
    # TODO: make these generic, preferably extractable from broadbean sequence object or smth
    number_of_markers = 1
    number_of_channels = 1


class RepeatingStaircaseRampGenerator(OneChannelOneMarkerGenerator):
    """
    Generates broadbean sequence for a staircase with a marker signal for
    triggering.
    """
    def __init__(self,
                 name: str,
                 **kwargs):
        super().__init__(name, **kwargs)

        # Base this class on the repeating staircase ramp object
        # ("inclusion" as opposed to "subclassing" is used in order to
        # decouple the implementation details of the staircase ramp object)
        self.add_submodule('staircase_ramp',
                           RepeatingStaircaseRamp('repeating_staircase_ramp')
                           )
        self.delegate_attr_objects.append('staircase_ramp')

        # Channel definitions
        # TODO: somewhere MAX VALUE has to meet the AWG channel number limit
        self.add_parameter(name='channel_number',
                           label='Signal channel number',
                           unit='',
                           get_cmd=None,
                           set_cmd=None,
                           get_parser=int,
                           initial_value=1,
                           vals=Numbers(min_value=1),
                           docstring="Number of the channel for the analog "
                                     "signal"
                           )
        # TODO: somewhere MAX VALUE has to meet the AWG marker channel number limit
        self.add_parameter(name='marker_channel_number',
                           label='Marker channel number',
                           unit='',
                           get_cmd=None,
                           set_cmd=None,
                           get_parser=int,
                           initial_value=1,
                           vals=Numbers(min_value=1),
                           docstring="Number of the channel for the marker "
                                     "signal within the analog channel"
                           )

        # Waveform generation specific parameters
        self.add_parameter(name='sample_rate',  # TODO: perhaps should be derived from AWG settings and limits
                           label='Sample rate',
                           unit='S/s',
                           get_cmd=None,
                           set_cmd=None,
                           get_parser=float,
                           initial_value=10e3,
                           vals=Numbers(min_value=0),
                           docstring="sample rate for AWG - we need it upfront for defining the broadbean sequence"
                           )
        self.add_parameter(name='settlement_time',
                           label='Time within step before trigger signal',
                           unit='s',
                           get_cmd=None,
                           set_cmd=None,
                           get_parser=float,
                           initial_value=1e-3,
                           vals=Numbers(min_value=0),
                           docstring="after this much time, the marker's "
                                     "falling edge occurs, hence the sample "
                                     "is acquired on hte lock-in this value depends on the system-under-measurement"
                           )
        self.add_parameter(name='lockin_integration_time',  # TODO: perhaps rename to smth lockin-independent
                           label='Time within step after trigger signal',
                           unit='s',
                           get_cmd=None,
                           set_cmd=None,
                           get_parser=float,
                           initial_value=1e-3,
                           vals=Numbers(min_value=0),
                           docstring="this much time WE THINK is required by "
                                     "the lockin for correctly acquiring one sample"
                           )
        self.add_parameter(name='restart_compensation',
                           label='Delay before the start of staircase',
                           unit='s',
                           get_cmd=None,
                           set_cmd=None,
                           get_parser=float,
                           initial_value=0,
                           vals=Numbers(min_value=0),
                           docstring="The very first step is made a bit longer "
                                     "in order to accommodate settlement "
                                     "required for the system when the "
                                     "staircase is restarted (i.e. when the "
                                     "jump is much bigger than the jump "
                                     "between individual steps)"
                           )

        # Convenient get-only parameters
        self.add_parameter(name='step_duration',
                           label='Step duration',
                           unit='#',
                           get_cmd=self._get_step_duration,
                           set_cmd=False,
                           get_parser=float,
                           vals=Numbers(),
                           docstring="Duration of a single step of the "
                                     "staircase"
                           )

    def _get_step_duration(self):
        return self.settlement_time() + self.lockin_integration_time()

    def get_trigger_moments_vector(self):
        return np.arange(
            self.settlement_time(),  # from
            self.n_all_steps() * self.step_duration(),  # until
            self.step_duration()  # distance between points
        )

    def make_broadbean_sequence(self) -> broadbean.Sequence:
        """
        Generates a broadbean sequence according to the set parameters.

        :return: Broadbean sequence object
        """
        # Create blueprint
        # this thing is called "waveform" within AWG
        staircase_blueprint = broadbean.BluePrint()
        staircase_blueprint.setSR(self.sample_rate())

        ramp = broadbean.PulseAtoms.ramp

        # Compensation for the restart of the staircase
        if self.restart_compensation() > 0:
            staircase_blueprint.insertSegment(
                -1,  # append to the end of the blueprint
                ramp,
                (self.start_ramp_voltage(), self.start_ramp_voltage()),  # plateau
                dur=self.restart_compensation(),
                name="staircase_restart_compensation"
            )

        for step_number, step_voltage in enumerate(
                np.linspace(self.start_ramp_voltage(),
                            self.finish_ramp_voltage(),
                            self.n_steps())):
            step_segment_name = f"fast_step_{step_number}_"

            # the analog plateau signal
            staircase_blueprint.insertSegment(
                -1,  # append to the end of the blueprint
                ramp, (step_voltage, step_voltage),  # flat plateau
                dur=self.step_duration(),
                name=step_segment_name
            )

            # the digital trigger signal
            # this trigger is set to AWG's marker channel, and its falling edge
            # will trigger acqusition of a sample on the lockin amplifier
            staircase_blueprint.setSegmentMarker(
                step_segment_name,
                (0, self.settlement_time()),
                self.marker_channel_number()
            )

        # Create an element out of the staircase blueprint

        staircase_element = broadbean.Element()
        staircase_element.addBluePrint(
            self.channel_number(), staircase_blueprint)

        # Create a sequence

        sequence = broadbean.Sequence()
        sequence.setSR(self.sample_rate())

        # Add the fast staircase element to the sequence

        waveform_id = 1
        sequence.addElement(waveform_id, staircase_element)
        sequence.setSequencingTriggerWait(waveform_id, 0)
        sequence.setSequencingNumberOfRepetitions(waveform_id, self.n_repetitions())
        # # infinite sequence - useful for debugging on hardware
        # sequence.setSequencingGoto(waveform_id, goto=waveform_id)

        return sequence