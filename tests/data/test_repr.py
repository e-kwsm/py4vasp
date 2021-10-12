from py4vasp.data import *
from py4vasp.raw import *
from py4vasp._util.convert import to_snakecase
from numpy import array


def test_repr(raw_data):
    tests = {
        Band: "multiple",
        Density: "Fe3O4 collinear",
        DielectricFunction: None,
        DielectricTensor: "dft",
        Dos: "Fe3O4",
        ElasticModulus: None,
        Energy: None,
        ForceConstants: "Sr2TiO4",
        Forces: "Sr2TiO4",
        InternalStrain: "Sr2TiO4",
        Kpoints: "line",
        Magnetism: "collinear",
        PiezoelectricTensor: None,
        Polarization: None,
        Projectors: "Fe3O4",
        Stress: "Sr2TiO4",
        Structure: "Fe3O4",
        Topology: "Fe3O4",
    }
    for class_, parameter in tests.items():
        raw = getattr(raw_data, to_snakecase(class_.__name__))(parameter)
        instance = class_(raw)
        copy = eval(repr(instance))
        assert copy.__class__ == class_
