from py4vasp.data import _util
import py4vasp.raw as raw
import py4vasp.exceptions as exception
import pytest


class RawData:
    version = _util._minimal_vasp_version


class DummyData(_util.Data):
    def __init__(self, raw_data):
        super().__init__(raw_data)

    @_util.require(raw.Version(_util._minimal_vasp_version.major + 1))
    def new_function(self):
        pass


def test_requirement_constructor():
    raw_data = RawData()
    data = DummyData(raw_data)
    with pytest.raises(exception.OutdatedVaspVersion):
        data.new_function()
    raw_data.version = raw.Version(raw_data.version.major - 1)
    with pytest.raises(exception.OutdatedVaspVersion):
        data = DummyData(raw_data)
