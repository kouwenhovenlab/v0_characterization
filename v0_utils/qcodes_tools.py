from typing import Type, Sequence

import qcodes
from qcodes import Instrument, Parameter
from qcodes.dataset.database import initialise_database
from qcodes.instrument.base import InstrumentBase


def instrument_factory(instrument_class, name, *args, **kwargs):
    """
    This is similar to pytopo->create_inst
    """
    try:
        instrument = Instrument.find_instrument(
            name, instrument_class=instrument_class)
        instrument.connect_message()  # call to print() is included in this method
        return instrument
    except KeyError:  # instrument with this name not found
        return instrument_class(name, *args, **kwargs)


def init_or_create_database(db_file_with_abs_path):
    # Let's work with a database file that is separate from QCoDeS default
    qcodes.config.core.db_location = db_file_with_abs_path
    initialise_database()


def load_or_create_experiment(experiment_name, sample_name):
    """
    This is similar to pytopo->select_experiment
    """
    try:
        experiment = qcodes.load_experiment_by_name(experiment_name,
                                                    sample_name)
    except ValueError as exception:
        if "Experiment not found" in str(exception):
            experiment = qcodes.new_experiment(experiment_name, sample_name)
        else:
            raise exception
    return experiment


def add_parameter_to_instrument(parameter: Type[Parameter],
                                instrument: Type[InstrumentBase]):
    """
    Adds an already existing parameter object to the given instrument object.

    This should become a method of the instrument class.
    """
    instrument.parameters.update(
        {parameter.name: parameter}
    )


class DelegateParameter(Parameter):
    """
    Hides a given parameter. This class is useful when, for example, hiding
    instrument channels into meaningful measured values like this: "voltage
    source, channel 1 voltage" -> "transistor gate voltage".

    qdev-wrappers contains a simpler version of this
    """
    def __init__(self, name: str, source: Parameter, *args, **kwargs):
        self._source = source

        if 'unit' not in kwargs:
            kwargs.update({'unit': self._source.unit})
        if 'label' not in kwargs:
            kwargs.update({'label': self._source.label})
        if 'snapshot_value' not in kwargs:
            kwargs.update({'snapshot_value': self._source._snapshot_value})

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
        return self._source

    def get_raw(self, *args, **kwargs):
        return self.source.get(*args, **kwargs)

    def set_raw(self, *args, **kwargs):
        self.source(*args, **kwargs)

    def snapshot_base(self, update: bool=False,
                      params_to_skip_update: Sequence[str]=None):
        snapshot = super().snapshot_base(
            update=update,
            params_to_skip_update=params_to_skip_update
        )
        snapshot.update(
            {'source_parameter': self._source.snapshot(update=update)}
        )
        return snapshot