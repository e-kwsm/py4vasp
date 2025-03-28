# Copyright © VASP Software GmbH,
# Licensed under the Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
import copy

from py4vasp._config import VASP_COLORS
from py4vasp._util import import_

from .contour import Contour
from .graph import Graph
from .mixin import Mixin
from .plot import plot
from .series import Series

go = import_.optional("plotly.graph_objects")
pio = import_.optional("plotly.io")

if import_.is_imported(go) and import_.is_imported(pio):
    axis_format = {"showexponent": "all", "exponentformat": "power"}
    contour = copy.copy(pio.templates["ggplot2"].data.contour[0])
    begin_red = [0, VASP_COLORS["red"]]
    middle_white = [0.5, "white"]
    end_blue = [1, VASP_COLORS["blue"]]
    contour.colorscale = [begin_red, middle_white, end_blue]
    data = {"contour": (contour,)}
    colorway = list(VASP_COLORS.values())
    layout = {"colorway": colorway, "xaxis": axis_format, "yaxis": axis_format}
    pio.templates["vasp"] = go.layout.Template(data=data, layout=layout)
    pio.templates["ggplot2"].layout.shapedefaults = {}
    pio.templates.default = "ggplot2+vasp"
