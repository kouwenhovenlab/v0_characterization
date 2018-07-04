"""
This module contains convenient functions and classes which simplify
interaction with QCoDeS features.

The members of this module might be candidates for integration into QCoDeS
codebase.
"""

from typing import Type, Sequence

import qcodes
from qcodes import Instrument, Parameter
from qcodes.dataset.database import initialise_database
from qcodes.dataset.experiment_container import Experiment
from qcodes.instrument.base import InstrumentBase


def instrument_factory(instrument_class: type,
                       name: str,
                       *args, **kwargs
                       ) -> Type[Instrument]:
    """
    Find an instrument with the given name of a given class, or create one if
    it is not found. If an instrument is found, a connection message is
    printed, as if the instrument has just been instantiated.

    Note: this function similar to pytopo.create_inst().

    Args:
        instrument_class
            Class of the instrument to find or create
        name
            Name of the instrument to find or create

    Returns:
        The found or created instrument
    """
    try:
        instrument = Instrument.find_instrument(
            name, instrument_class=instrument_class)
        instrument.connect_message()  # prints the message
    except KeyError as exception:
        if "has been removed" in str(exception):
            instrument = instrument_class(name, *args, **kwargs)
        else:
            raise exception
    return instrument


def init_or_create_database(db_file_with_abs_path: str) -> None:
    """
    This function sets up QCoDeS to refer to the given database file. If the
    database file does not exist, it will be initiated.

    Args:
        db_file_with_abs_path
            Database file name with absolute path, for example
            "C:\mydata\majorana_experiments.db"
    """
    qcodes.config.core.db_location = db_file_with_abs_path
    initialise_database()


def load_or_create_experiment(experiment_name: str,
                              sample_name: str
                              ) -> Experiment:
    """
    Find and return an experiment with the given name and sample name,
    or create one if not found.

    Note: this function similar to pytopo.select_experiment().

    Args:
        experiment_name
            Name of the experiment to find or create
        sample_name
            Name of the sample

    Returns:
        The found or created experiment
    """
    try:
        experiment = qcodes.load_experiment_by_name(experiment_name,
                                                    sample_name)
    except ValueError as exception:
        if "Experiment not found" in str(exception):
            experiment = qcodes.new_experiment(experiment_name,
                                               sample_name)
        else:
            raise exception
    return experiment


def add_parameter_to_instrument(parameter: Type[Parameter],
                                instrument: Type[InstrumentBase]) -> None:
    """
    Adds an already existing parameter object to the given instrument object.

    Note: this should become a method of the instrument class.

    Args:
        parameter
            The parameter object that is to be added to the instrument
        instrument
            The instrument object where the parameter is to be added to
    """
    instrument.parameters.update(
        {parameter.name: parameter}
    )


class DelegateParameter(Parameter):
    """
    Delegate parameter redirects calls to `get` and `set` methods to the
    source parameter, but may have name, unit, label, etc. that are
    different from the source parameter.

    This object is very useful when one prefers to operate on a parameter
    that has a clear meaning in the experimental context rather than on a
    parameter that refers to an instrument that is used during the
    measurement. For example, if the channel `ch2` of an instrument `inst1`
    is connected to the gate of a transistor, then in order to set the gate
    voltage to 1.5V, one has to write `inst1.ch2(1.5)` - it is not obvious
    from this line that the gate of a transistor is changed. Instead, if one
    uses a `DelegateParameter` called `v_gate` that has `inst1.ch2` as its
    source, the line of code that sets the gate voltage to 1.5V would be
    `v_gate(1.5)` (or `v_gate.set(1.5)`) which does the same as
    `inst1.ch2(1.5)` while it is absolutely clear from the code what is being
    done.

    Importantly enough, the metadata of the `DelegateParameter` includes
    the metadata of the source parameter.

    The `DelegateParameter` attributes like unit and label will be the same
    as of the source parameter, unless explicitly specified.

    Note: qdev-wrappers contains a simpler version of this class.

    Args:
        name
            Name of the DelegateParameter
        source
            Source Parameter object
    """

    def __init__(self, name: str, source: Parameter, *args, **kwargs):
        self._source_parameter = source

        if 'unit' not in kwargs:
            kwargs.update({'unit': self._source_parameter.unit})
        if 'label' not in kwargs:
            kwargs.update({'label': self._source_parameter.label})
        if 'snapshot_value' not in kwargs:
            kwargs.update(
                {'snapshot_value': self._source_parameter._snapshot_value})

        if 'set_cmd' in kwargs:
            raise KeyError('It is not allowed to set "set_cmd" of a '
                           'DelegateParameter because the one of the source '
                           'parameter is supposed to be used.')
        if 'get_cmd' in kwargs:
            raise KeyError('It is not allowed to set "get_cmd" of a '
                           'DelegateParameter because the one of the source '
                           'parameter is supposed to be used.')

        super().__init__(name=name, *args, **kwargs)

    @property
    def source(self):
        return self._source_parameter

    def get_raw(self, *args, **kwargs):
        return self.source.get(*args, **kwargs)

    def set_raw(self, *args, **kwargs):
        self.source(*args, **kwargs)

    def snapshot_base(self,
                      update: bool = False,
                      params_to_skip_update: Sequence[str] = None):
        snapshot = super().snapshot_base(
            update=update,
            params_to_skip_update=params_to_skip_update
        )
        snapshot.update(
            {'source_parameter': self._source_parameter.snapshot(update=update)}
        )
        return snapshot
