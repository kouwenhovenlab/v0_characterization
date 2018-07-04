# Useful tools
import numpy as np
from typing import Type

# qcodes features
from qcodes import Instrument, Parameter
# a separate database during development of this scripts

# Drivers
from qcodes.instrument_drivers.tektronix.AWG70000A import AWG70000A
from qcodes.instrument_drivers.tektronix.AWG70000A import _chan_resolutions \
    as awg_channel_resolutions

# Broadbean module for defining signals emitted by AWG
import broadbean
from broadbean.plotting import plotter as broadbean_plotter

from qcodes.utils.validators import Numbers


# TODO: decide what to do with class parameters - make them get-only Parameters? or create a naming convention?


################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################





class StaircaseRamp(Instrument):
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




###############################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################



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





################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################


class AwgSequencer(Instrument):
    def __init__(self,
                 name: str,
                 awg_obj: Type[AWG70000A],
                 sequence_gen_obj: Type[SequenceGenerator],
                 **kwargs):
        super().__init__(name, **kwargs)

        self.add_submodule(name='awg',
                           submodule=awg_obj)

        self.add_submodule(name='sequence_gen',
                           submodule=sequence_gen_obj)

        self.delegate_attr_objects = ['awg', 'sequence_gen']


class OneChannelOneMarkerAwgSequencer(AwgSequencer):
    def __init__(self,
                 name: str,
                 awg_obj: Type[AWG70000A],
                 sequence_gen_obj: Type[OneChannelOneMarkerGenerator],
                 **kwargs):
        super().__init__(name, awg_obj, sequence_gen_obj, **kwargs)

        # TODO: AGAIN, WHAT IS THIS???
        self.add_parameter(name='channel_p_p_amplitude_factor',
                           label='Channel peak-to-peak amplitude at AWG',
                           unit='V',  # TODO: is it correct?
                           get_cmd=None,
                           set_cmd=None,
                           get_parser=float,
                           initial_value=1.0,
                           vals=Numbers(),
                           docstring="It is that '2/f' thing for converting "
                                     "broadbean a.u. into voltage."
                                     "Value of '1' means that '1' a.u. in "
                                     "broadbean sequence == '1 V' in AWG."
                           )
        # TODO: AGAIN, WHAT IS THIS???
        self.add_parameter(name='channel_amplitude_forging',
                           label='Channel amplitude for forging sequence',
                           unit='V',  # TODO: is it correct?
                           get_cmd=None,
                           set_cmd=None,
                           get_parser=float,
                           initial_value=1.0,
                           vals=Numbers(),
                           docstring="In general case, this should be a list "
                                     "of aplitudes for each used channel in "
                                     "the broadbean sequence."
                           )
        self.add_parameter(name='marker_channel_high',
                           label='Marker channel high',
                           unit='V',
                           get_cmd=self._get_marker_high,
                           set_cmd=self._set_marker_high,
                           get_parser=float,
                           initial_value=1.75,
                           vals=Numbers(),
                           docstring="The marker high value for the marker "
                                     "channel within the analog channel."
                           )
        self.add_parameter(name='marker_channel_low',
                           label='Marker channel low',
                           unit='V',
                           get_cmd=self._get_marker_low,
                           set_cmd=self._set_marker_low,
                           get_parser=float,
                           initial_value=0.0,
                           vals=Numbers(),
                           docstring="The marker low value for the marker "
                                     "channel within the analog channel."
                           )

    def _get_channel_resolution(self):
        return max(awg_channel_resolutions[self.awg.model])

    def _get_channel_obj(self):
        return self.awg.channels[self.sequence_gen.channel_number() - 1]

    def _get_parameter_obj_of_marker(self, subname: str) -> Parameter:
        """
        ...

        Args:
            subname
                stuff like "high", "low", etc (in order to generate the name
                of a callable like "marker{marker_channel_number}_{subname}"
        """
        return getattr(
            self._get_channel_obj(),
            f"marker{self.sequence_gen.marker_channel_number()}_{subname}"
        )

    def _get_marker_high(self):
        return self._get_parameter_obj_of_marker("high")()

    def _set_marker_high(self, marker_high):
        self._get_parameter_obj_of_marker("high")(marker_high)

    def _get_marker_low(self):
        return self._get_parameter_obj_of_marker("low")()

    def _set_marker_low(self, marker_low):
        self._get_parameter_obj_of_marker("low")(marker_low)

    def _get_forged_sequence(self):
        sequence_obj = self.sequence_gen.make_broadbean_sequence()
        forged_sequence = sequence_obj.forge()
        return forged_sequence

    def _send_sequence_to_awg_and_load(self) -> None:
        """
        .....
        """
        # forge the sequence
        forged_sequence = self._get_forged_sequence()

        # create a sequence file
        seqx_file = self.awg.make_SEQX_from_forged_sequence(
            forged_sequence,
            np.atleast_1d(self.channel_amplitude_forging()),
            self.sequence_gen.sequence_name)
        seqx_file_name = f'{self.sequence_gen.sequence_name}.seqx'

        # clear lists of sequences and waveforms on the instrument in order
        # to prevent cluttering
        self.awg.stop()
        self.awg.clearSequenceList()
        self.awg.clearWaveformList()

        # send the sequence file to the instrument and load it
        self.awg.sendSEQXFile(seqx_file, filename=seqx_file_name)
        self.awg.loadSEQXFile(seqx_file_name)

    def _setup_awg_channels_for_sequence(self) -> None:
        """
        ..........
        """
        self.awg.sample_rate(self.sequence_gen.sample_rate())

        channel_obj = self._get_channel_obj()

        # Add sequence to the channel
        track_number = 1
        channel_obj.setSequenceTrack(self.sequence_gen.sequence_name, track_number)

        channel_obj.awg_amplitude(self.channel_p_p_amplitude_factor())

        # We reserve 15 bits for the analog channel so we have 1 bit for marker 1
        channel_obj.resolution(
            self._get_channel_resolution() - self.sequence_gen.number_of_markers)

        channel_obj.state(1)  # means "on"

    def send_sequence_and_setup_awg(self) -> None:
        """
        This performs the physical action of generation the sequence from
        the sequence generator, forging it, sending it as a sequence file
        to AWG, loading it, and assigning to channel.

        It is very useful to add this as a "before_run" for "Measurement"
        """
        self._send_sequence_to_awg_and_load()
        self._setup_awg_channels_for_sequence()





################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################






class HardwareSweep(Instrument):
    def run(self):
        raise NotImplementedError("Subclasses of HardwareSweep should "
                                  "implement run method")




################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################







################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################







################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################







################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################

