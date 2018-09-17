"""
This module contains the infrastructure classes for correct loading of
broadbean sequence objects produced by sequence generators to AWG devices.
"""

from typing import Type

import numpy as np
from qcodes import Parameter
from qcodes.instrument_drivers.tektronix.AWG70000A import AWG70000A, \
    _chan_resolutions as awg_channel_resolutions
from qcodes.utils.validators import Numbers

from .qcodes_tools import VirtualInstrument
from .sequence_generators import SequenceGenerator, \
    OneChannelOneMarkerGenerator, \
    OneChannelTwoMarkerGenerator


class AwgSequencer(VirtualInstrument):
    """
    This is the base class of an AWG sequencer. The goal of this class is to
    encapsulate the logic of sending a broadbean sequence object to an AWG
    instrument. This instrument contains AWG and a sequence generator as its
    submodules.
    """

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

    def send_sequence_and_setup_awg(self) -> None:
        """
        This method shall perform the action of generating the sequence from
        the sequence generator, forging it, sending it as a sequence file to
        AWG, loading it, and assigning to channels.

        It is very useful to add this as a "before_run" for "Measurement"
        """
        raise NotImplementedError("AwgSequencer must implement this method")


class OneChannelOneMarkerAwgSequencer(AwgSequencer):
    """
    An AWG sequence virtual instrument that uploads broadbean sequences
    that contain only one analog channel and one marker channel (that is
    attached to it).
    """

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
                           initial_value=1.4,
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
        channel_obj.setSequenceTrack(self.sequence_gen.sequence_name,
                                     track_number)

        channel_obj.awg_amplitude(self.channel_p_p_amplitude_factor())

        # We reserve 15 bits for the analog channel, so that we have 1 bit for
        # the marker 1
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

        
class OneChannelTwoMarkerAwgSequencer(AwgSequencer):
    """
    An AWG sequence virtual instrument that uploads broadbean sequences
    that contain only one analog channel and two marker channels (that is
    attached to it).
    """

    def __init__(self,
                 name: str,
                 awg_obj: Type[AWG70000A],
                 sequence_gen_obj: Type[OneChannelTwoMarkerGenerator],
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
        self.add_parameter(name='marker_falling_channel_high',
                           label='Marker falling channel high',
                           unit='V',
                           get_cmd=self._get_marker_falling_high,
                           set_cmd=self._set_marker_falling_high,
                           get_parser=float,
                           initial_value=1.4,
                           vals=Numbers(),
                           docstring="The marker high value for the marker "
                                     "channel for the falling edge within the analog channel."
                           )
        self.add_parameter(name='marker_rising_channel_high',
                           label='Marker rising channel high',
                           unit='V',
                           get_cmd=self._get_marker_rising_high,
                           set_cmd=self._set_marker_rising_high,
                           get_parser=float,
                           initial_value=1.7,
                           vals=Numbers(),
                           docstring="The marker high value for the marker "
                                     "channel for the rising edge within the analog channel."
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

    def _get_parameter_obj_of_marker_falling(self, subname: str) -> Parameter:
        """
        ...

        Args:
            subname
                stuff like "high", "low", etc (in order to generate the name
                of a callable like "marker{marker_channel_number}_{subname}"
        """
        return getattr(
            self._get_channel_obj(),
            f"marker{self.sequence_gen.marker_falling_channel_number()}_{subname}"
        )

    def _get_marker_falling_high(self):
        return self._get_parameter_obj_of_marker_falling("high")()

    def _set_marker_falling_high(self, marker_high):
        self._get_parameter_obj_of_marker_falling("high")(marker_high)

    def _get_marker_falling_low(self):
        return self._get_parameter_obj_of_marker_falling("low")()

    def _set_marker_falling_low(self, marker_low):
        self._get_parameter_obj_of_marker_falling("low")(marker_low)
        
    def _get_parameter_obj_of_marker_rising(self, subname: str) -> Parameter:
        """
        ...

        Args:
            subname
                stuff like "high", "low", etc (in order to generate the name
                of a callable like "marker{marker_channel_number}_{subname}"
        """
        return getattr(
            self._get_channel_obj(),
            f"marker{self.sequence_gen.marker_rising_channel_number()}_{subname}"
        )

    def _get_marker_rising_high(self):
        return self._get_parameter_obj_of_marker_rising("high")()

    def _set_marker_rising_high(self, marker_high):
        self._get_parameter_obj_of_marker_rising("high")(marker_high)

    def _get_marker_rising_low(self):
        return self._get_parameter_obj_of_marker_rising("low")()

    def _set_marker_rising_low(self, marker_low):
        self._get_parameter_obj_of_marker_rising("low")(marker_low)
        
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
        channel_obj.setSequenceTrack(self.sequence_gen.sequence_name,
                                     track_number)

        channel_obj.awg_amplitude(self.channel_p_p_amplitude_factor())

        # We reserve 14 bits for the analog channel, so that we have 2 bits for
        # the markers 1 and 2
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

        