# Copyright © VASP Software GmbH,
# Licensed under the Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
import numpy as np

from py4vasp import _config, exception
from py4vasp._third_party import view
from py4vasp._util import documentation
from py4vasp.calculation import _base, _slice, _structure

_index_note = """\
Notes
-----
The index order is different compared to the raw data when noncollinear calculations
are used. This routine returns the magnetic moments as (steps, atoms, orbitals,
directions)."""

_moment_selection = """\
selection : str
    If VASP was run with LORBMOM = T, the orbital moments are computed and the routine
    will default to the total moments. You can specify "spin" or "orbital" to select
    the individual contributions instead.
"""


@documentation.format(examples=_slice.examples("magnetism"))
class Magnetism(_slice.Mixin, _base.Refinery, _structure.Mixin, view.Mixin):
    """The local moments describe the charge and magnetization near an atom.

    The projection on local moments is particularly relevant in the context of
    magnetic materials. It analyzes the electronic states in the vicinity of an
    atom by projecting the electronic orbitals onto the localized projectors of
    the PAWs. The local moments help understanding the magnetic ordering, the spin
    polarization, and the influence of neighboring atoms on the magnetic behavior.

    This class allows to access the computed moments from a VASP calculation.
    Remember that VASP calculates the projections only if you need to set
    :tag:`LORBIT` in the INCAR file. If the system is computed without spin
    polarization, the resulting moments correspond only to the local charges
    resolved by angular momentum. For collinear calculation, additionally the
    magnetic moment are computed. In noncollinear calculations, the magnetization
    becomes a vector. When comparing the results extracted from VASP to experimental
    observation, please be aware that the finite size of the radius in the projection
    may influence the observed moments. Hence, there is no one-to-one correspondence
    to the experimental moments.

    {examples}
    """

    _missing_data_message = "Atom resolved magnetic information not present, please verify LORBIT tag is set."

    length_moments = 1.5
    "Length in Å how a magnetic moment is displayed relative to the largest moment."

    @_base.data_access
    def __str__(self):
        magmom = "MAGMOM = "
        moments_last_step = self.total_moments()
        moments_to_string = lambda vec: " ".join(f"{moment:.2f}" for moment in vec)
        if moments_last_step is None:
            return "not spin polarized"
        elif moments_last_step.ndim == 1:
            return magmom + moments_to_string(moments_last_step)
        else:
            separator = " \\\n         "
            generator = (moments_to_string(vec) for vec in moments_last_step)
            return magmom + separator.join(generator)

    @_base.data_access
    @documentation.format(
        index_note=_index_note, examples=_slice.examples("magnetism", "to_dict")
    )
    def to_dict(self):
        """Read the charges and magnetization data into a dictionary.

        Returns
        -------
        dict
            Contains the charges and magnetic moments generated by VASP projected
            on atoms and orbitals.

        {index_note}

        {examples}
        """
        return {
            "charges": self.charges(),
            "moments": self.moments(),
            **self._add_spin_and_orbital_moments(),
        }

    @_base.data_access
    @documentation.format(
        selection=_moment_selection, examples=_slice.examples("magnetism", "to_view")
    )
    def to_view(self, selection="total", supercell=None):
        """Visualize the magnetic moments as arrows inside the structure.

        Parameters
        ----------
        {selection}

        Returns
        -------
        View
            Contains the atoms and the unit cell as well as an arrow indicating the
            strength of the magnetic moment. If noncollinear magnetism is used
            the moment points in the actual direction; for collinear magnetism
            the moments are aligned along the z axis by convention.

        {examples}
        """
        viewer = self._structure[self._steps].plot(supercell)
        moments = self._prepare_magnetic_moments_for_plotting(selection)
        if moments is not None:
            ion_arrows = view.IonArrow(
                quantity=moments,
                label=f"{selection} moments",
                color=_config.VASP_COLORS["blue"],
                radius=0.2,
            )
            viewer.ion_arrows = [ion_arrows]
        return viewer

    @_base.data_access
    @documentation.format(examples=_slice.examples("magnetism", "charges"))
    def charges(self):
        """Read the charges of the selected steps.

        Returns
        -------
        np.ndarray
            Contains the charges for the selected steps projected on atoms and orbitals.

        {examples}
        """
        self._raise_error_if_steps_out_of_bounds()
        return self._raw_data.spin_moments[self._steps, 0]

    @_base.data_access
    @documentation.format(
        selection=_moment_selection,
        index_note=_index_note,
        examples=_slice.examples("magnetism", "moments"),
    )
    def moments(self, selection="total"):
        """Read the magnetic moments of the selected steps.

        Parameters
        ----------
        {selection}

        Returns
        -------
        np.ndarray
            Contains the magnetic moments for the selected steps projected on atoms and
            orbitals.

        {index_note}

        {examples}
        """
        self._raise_error_if_steps_out_of_bounds()
        self._raise_error_if_selection_not_available(selection)
        if self._only_charge:
            return None
        elif self._spin_polarized:
            return self._collinear_moments()
        else:
            return self._noncollinear_moments(selection)

    @_base.data_access
    @documentation.format(examples=_slice.examples("magnetism", "total_charges"))
    def total_charges(self):
        """Read the total charges of the selected steps.

        Returns
        -------
        np.ndarray
            Contains the total charges for the selected steps projected on atoms. This
            corresponds to the charges summed over the orbitals.

        {examples}
        """
        return _sum_over_orbitals(self.charges())

    @_base.data_access
    @documentation.format(
        selection=_moment_selection,
        index_note=_index_note,
        examples=_slice.examples("magnetism", "total_moments"),
    )
    def total_moments(self, selection="total"):
        """Read the total magnetic moments of the selected steps.

        Parameters
        ----------
        {selection}

        Returns
        -------
        np.ndarray
            Contains the total magnetic moments for the selected steps projected on atoms.
            This corresponds to the magnetic moments summed over the orbitals.

        {index_note}

        {examples}
        """
        return _sum_over_orbitals(self.moments(selection), is_vector=self._noncollinear)

    @property
    def _only_charge(self):
        return self._raw_data.spin_moments.shape[1] == 1

    @property
    def _spin_polarized(self):
        return self._raw_data.spin_moments.shape[1] == 2

    @property
    def _noncollinear(self):
        return self._raw_data.spin_moments.shape[1] == 4

    @property
    def _has_orbital_moments(self):
        return not self._raw_data.orbital_moments.is_none()

    def _collinear_moments(self):
        return self._raw_data.spin_moments[self._steps, 1]

    def _noncollinear_moments(self, selection):
        spin_moments = self._raw_data.spin_moments[self._steps, 1:]
        if self._has_orbital_moments:
            orbital_moments = self._raw_data.orbital_moments[self._steps, 1:]
        else:
            orbital_moments = np.zeros_like(spin_moments)
        if selection == "orbital":
            moments = orbital_moments
        elif selection == "spin":
            moments = spin_moments
        else:
            moments = spin_moments + orbital_moments
        direction_axis = 1 if moments.ndim == 4 else 0
        return np.moveaxis(moments, direction_axis, -1)

    def _add_spin_and_orbital_moments(self):
        if not self._has_orbital_moments:
            return {}
        spin_moments = self._raw_data.spin_moments[self._steps, 1:]
        orbital_moments = self._raw_data.orbital_moments[self._steps, 1:]
        direction_axis = 1 if spin_moments.ndim == 4 else 0
        return {
            "spin_moments": np.moveaxis(spin_moments, direction_axis, -1),
            "orbital_moments": np.moveaxis(orbital_moments, direction_axis, -1),
        }

    def _prepare_magnetic_moments_for_plotting(self, selection):
        moments = self.total_moments(selection)
        moments = self._make_sure_moments_have_timestep_dimension(moments)
        moments = _convert_moment_to_3d_vector(moments)
        max_length_moments = _max_length_moments(moments)
        if max_length_moments > 1e-15:
            rescale_moments = Magnetism.length_moments / max_length_moments
            return rescale_moments * moments
        else:
            return None

    def _make_sure_moments_have_timestep_dimension(self, moments):
        if not self._is_slice and moments is not None:
            moments = moments[np.newaxis]
        return moments

    def _raise_error_if_steps_out_of_bounds(self):
        try:
            np.zeros(self._raw_data.spin_moments.shape[0])[self._steps]
        except IndexError as error:
            raise exception.IncorrectUsage(
                f"Error reading the magnetic moments. Please check if the steps "
                f"`{self._steps}` are properly formatted and within the boundaries."
            ) from error

    def _raise_error_if_selection_not_available(self, selection):
        if selection not in ("spin", "orbital", "total"):
            raise exception.IncorrectUsage(
                f"The selection {selection} is incorrect. Please check if it is spelled "
                "correctly. Possible choices are total, spin, or orbital."
            )
        if selection != "orbital" or self._has_orbital_moments:
            return
        raise exception.NoData(
            "There are no orbital moments in the VASP output. Please make sure that you "
            "run the calculation with LORBMOM = T and LSORBIT = T."
        )


def _sum_over_orbitals(quantity, is_vector=False):
    if quantity is None:
        return None
    if is_vector:
        return np.sum(quantity, axis=-2)
    return np.sum(quantity, axis=-1)


def _convert_moment_to_3d_vector(moments):
    if moments is not None and moments.ndim == 2:
        moments = moments.reshape((*moments.shape, 1))
        no_new_moments = (0, 0)
        add_zero_for_xy_axis = (2, 0)
        padding = (no_new_moments, no_new_moments, add_zero_for_xy_axis)
        moments = np.pad(moments, padding)
    return moments


def _max_length_moments(moments):
    if moments is not None:
        return np.max(np.linalg.norm(moments, axis=2))
    else:
        return 0.0
