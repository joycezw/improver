# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2017 Met Office.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
"""Module to apply a recursive filter to neighbourhooded data."""

import iris
import numpy as np

from improver.nbhood.square_kernel import SquareNeighbourhood
from improver.utilities.cube_checker import check_cube_coordinates


class RecursiveFilter(object):

    """
    Apply a recursive filter to the input cube.
    """

    def __init__(self, alpha_x=None, alpha_y=None, iterations=None,
                 edge_width=1):
        """
        Initialise the class.

        Keyword Args:
            alpha_x (Float or None):
                Filter parameter: A constant used to weight the
                recursive filter along the x-axis. Defined such
                that 0 <= alpha_x < 1.0
            alpha_y (Float or None):
                Filter parameter: A constant used to weight the
                recursive filter along the y-axis. Defined such
                that 0 <= alpha_y < 1.0
            iterations (integer or None):
                The number of iterations of the recursive filter.
            edge_width (integer):
                The width of the padding applied to the grid cells
                when adding the SquareNeighbourhood halo.

        Raises:
            ValueError: If alpha_x is not set such that 0 <= alpha_x < 1
            ValueError: If alpha_y is not set such that 0 <= alpha_y < 1
            ValueError: If number of iterations is not None and is set such
                        that iterations is not >= 1

        """

        if alpha_x is not None:
            if not 0 <= alpha_x < 1:
                raise ValueError(
                    "Invalid alpha_x: must be >= 0 and < 1: {}".format(
                        alpha_x))

        if alpha_y is not None:
            if not 0 <= alpha_y < 1:
                raise ValueError(
                    "Invalid alpha_y: must be >= 0 and < 1: {}".format(
                        alpha_y))

        if iterations is not None:
            if not iterations >= 1:
                raise ValueError(
                    "Invalid number of iterations: must be >= 1: {}".format(
                        iterations))

        self.alpha_x = alpha_x
        self.alpha_y = alpha_y
        self.iterations = iterations
        self.edge_width = edge_width

    def __repr__(self):
        """Represent the configured plugin instance as a string."""
        result = ('<RecursiveFilter: alpha_x: {}, alpha_y: {}, iterations: {},'
                  ' edge_width: {}')
        return result.format(self.alpha_x, self.alpha_y, self.iterations,
                             self.edge_width)

    @staticmethod
    def recurse_forward_x(grid, alphas):
        """
        Method to run the recursive filter in the forward x-direction.

        In the forward direction:
            Recursive filtering is calculated as:
                Bi = ((1-alpha) * Ai) + (alpha * Bi-1)

            Progressing from gridpoint i-1 to i:
                Bi = new value at gridpoint i, Ai = Old value at gridpoint i
                Bi-1 = New value at gridpoint i-1

        Args:
            grid (numpy array):
                Array containing the input data to which the recursive filter
                will be applied.
            alphas (numpy array):
                Array of alpha values that will be used when applying
                the recursive filter along the x-axis.

        Returns:
            grid (numpy array):
                Array containing the smoothed field after the recursive
                filter method has been applied to the input array in the
                forward x-direction.
        """

        x_lim = grid.shape[0]
        for i in range(1, x_lim):
            grid[i, :] = ((1. - alphas[i, :]) * grid[i, :] +
                          alphas[i, :] * grid[i-1, :])
        return grid

    @staticmethod
    def recurse_backwards_x(grid, alphas):
        """
        Method to run the recursive filter in the backwards x-direction.

        In the backwards direction:
            Recursive filtering is calculated as:
                Bi = ((1-alpha) * Ai) + (alpha * Bi+1)

            Progressing from gridpoint i+1 to i:
                Bi = new value at gridpoint i, Ai = Old value at gridpoint i
                Bi+1 = New value at gridpoint i+1

        Args:
            grid (numpy array):
                Array containing the input data to which the recursive filter
                will be applied.
            alphas (numpy array):
                Array of alpha values that will be used when applying
                the recursive filter along the x-axis.

        Returns:
            grid (numpy array):
                Array containing the smoothed field after the recursive
                filtermethod has been applied to the input array in the
                backwards x-direction.
        """

        x_lim = grid.shape[0]
        for i in range(x_lim-2, -1, -1):
            grid[i, :] = ((1. - alphas[i, :]) * grid[i, :] +
                          alphas[i, :] * grid[i+1, :])
        return grid

    @staticmethod
    def recurse_forward_y(grid, alphas):
        """
        Method to run the recursive filter in the forward y-direction.

        In the forward direction:
            Recursive filtering is calculated as:
                Bi = ((1-alpha) * Ai) + (alpha * Bi-1)

            Progressing from gridpoint i-1 to i:
                Bi = new value at gridpoint i, Ai = Old value at gridpoint i
                Bi-1 = New value at gridpoint i-1

        Args:
            grid (numpy array):
                Array containing the input data to which the recursive filter
                will be applied.
            alphas (numpy array):
                Array of alpha values that will be used when applying
                the recursive filter along the y-axis.

        Returns:
            grid (numpy array):
                Array containing the smoothed field after the recursive
                filter method has been applied to the input array in the
                forward y-direction.
        """

        y_lim = grid.shape[1]
        for i in range(1, y_lim):
            grid[:, i] = ((1. - alphas[:, i]) * grid[:, i] +
                          alphas[:, i] * grid[:, i-1])
        return grid

    @staticmethod
    def recurse_backwards_y(grid, alphas):
        """
        Method to run the recursive filter in the backwards y-direction.

        In the backwards direction:
            Recursive filtering is calculated as:
                Bi = ((1-alpha) * Ai) + (alpha * Bi+1)

            Progressing from gridpoint i+1 to i:.
                Bi = new value at gridpoint i, Ai = Old value at gridpoint i
                Bi+1 = New value at gridpoint i+1

        Args:
            grid (numpy array):
                Array containing the input data to which the recursive filter
                will be applied.
            alphas (numpy array):
                Array of alpha values that will be used when applying
                the recursive filter along the y-axis.

        Returns:
            grid (numpy array):
                Array containing the smoothed field after the recursive
                filter method has been applied to the input array in the
                backwards y-direction.
        """

        y_lim = grid.shape[1]
        for i in range(y_lim-2, -1, -1):
            grid[:, i] = ((1. - alphas[:, i]) * grid[:, i] +
                          alphas[:, i] * grid[:, i+1])
        return grid

    @staticmethod
    def run_recursion(cube, alphas_x, alphas_y, iterations):
        """
        Method to run the recursive filter.

        Args:
            cube (Iris.cube.Cube):
                Cube containing the input data to which the recursive filter
                will be applied.
            alphas_x (Iris.cube.Cube):
                Cube containing array of alpha values that will be used
                when applying the recursive filter along the x-axis.
            alphas_y (Iris.cube.Cube):
                Cube containing array of alpha values that will be used
                when applying the recursive filter along the y-axis.
            iterations (integer):
                The number of iterations of the recursive filter

        Returns:
            cube (Iris.cube.Cube):
                Cube containing the smoothed field after the recursive filter
                method has been applied to the input cube.
        """

        output = cube.data
        for _ in range(iterations):
            output = RecursiveFilter.recurse_forward_x(output,
                                                       alphas_x.data)
            output = RecursiveFilter.recurse_backwards_x(output,
                                                         alphas_x.data)
            output = RecursiveFilter.recurse_forward_y(output,
                                                       alphas_y.data)
            output = RecursiveFilter.recurse_backwards_y(output,
                                                         alphas_y.data)
            cube.data = output
        return cube

    def set_alphas(self, cube, alpha, alphas_cube):
        """
        Set up the alpha parameter.

        Args:
            cube (Iris.cube.Cube):
                Cube containing the input data to which the recursive filter
                will be applied.
            alpha (Float):
                The constant used to weight the recursive filter in that
                direction: Defined such that 0.0 <= alpha <= 1.0
            alphas_cube (Iris.cube.Cube or None):
                Cube containing array of alpha values that will be used
                when applying the recursive filter in a specific direction.

        Raises:
            ValueError: If alpha and alphas_cube are both set to None
            ValueError: If dimension of alphas array is less than dimension
                        of data array
            ValueError: If dimension of alphas array is greater than dimension
                        of data array

        Returns:
            alphas_cube (Iris.cube.Cube):
                Cube containing a padded array of alpha values
                for the specified direction.
        """

        if alphas_cube is None:
            if alpha is None:
                emsg = ("A value for alpha must be set if alphas_cube is "
                        "set to None: alpha is currently set as: {}")
                raise ValueError(emsg.format(alpha))
            alphas_cube = cube.copy(
                data=np.ones(cube.data.shape) * alpha)

        if alphas_cube is not None:
            if alphas_cube.data.shape != cube.data.shape:
                emsg = ("Dimensions of alphas array do not match dimensions "
                        "of data array: {} < {}")
                raise ValueError(emsg.format(alphas_cube.data.shape,
                                             cube.data.shape))

        alphas_cube = SquareNeighbourhood().pad_cube_with_halo(
            alphas_cube, self.edge_width, self.edge_width)
        return alphas_cube

    def process(self, cube, alphas_x=None, alphas_y=None):
        """
        Set up the alpha parameters and run the recursive filter.

        The steps undertaken are:

        1. Split the input cube into slices determined by the co-ordinates in
           the x and y directions.
        2. Construct an array of filter parameters (alphas_x and alphas_y) for
           each cube slice that are used to weight the recursive filter in
           the x- and y-directions.
        3. Pad each cube slice with a square-neighbourhood halo and apply
           the recursive filter for the required number of iterations.
        4. Remove the halo from the cube slice and append the recursed cube
           slice to a 'recursed cube'.
        5. Merge all the cube slices in the 'recursed cube' into a 'new cube'.
        6. Modify the 'new cube' so that its scalar dimension co-ordinates are
           consistent with those in the original input cube.
        7. Return the 'new cube' which now contains the recursively filtered
           values for the original input cube.

        Args:
            cube (Iris.cube.Cube):
                Cube containing the input data to which the recursive filter
                will be applied.

        Keyword Args:
            alphas_x (Iris.cube.Cube or None):
                Cube containing array of alpha values that will be used when
                applying the recursive filter along the x-axis.
            alphas_y (Iris.cube.Cube or None):
                Cube containing array of alpha values that will be used when
                applying the recursive filter along the y-axis.

        Returns:
            new_cube (Iris.cube.Cube):
                Cube containing the smoothed field after the recursive filter
                method has been applied.
        """

        cube_format = next(cube.slices([cube.coord(axis='y'),
                                        cube.coord(axis='x')]))
        alphas_x = self.set_alphas(cube_format, self.alpha_x, alphas_x)
        alphas_y = self.set_alphas(cube_format, self.alpha_y, alphas_y)

        recursed_cube = iris.cube.CubeList()
        for output in cube.slices([cube.coord(axis='y'),
                                   cube.coord(axis='x')]):

            padded_cube = SquareNeighbourhood().pad_cube_with_halo(
                output, self.edge_width, self.edge_width)
            new_cube = self.run_recursion(padded_cube, alphas_x, alphas_y,
                                          self.iterations)
            new_cube = SquareNeighbourhood().remove_halo_from_cube(
                new_cube, self.edge_width, self.edge_width)
            recursed_cube.append(new_cube)

        new_cube = recursed_cube.merge_cube()
        new_cube = check_cube_coordinates(cube, new_cube)
        return new_cube
