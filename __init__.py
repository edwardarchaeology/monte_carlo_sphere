"""
3D Monte Carlo π Approximation

A desktop GUI application demonstrating Monte Carlo estimation of π
using 3D random sampling with interactive visualization.
"""

__version__ = "1.0.0"
__author__ = "Monte Carlo Team"
__all__ = ["MonteCarloPi3D", "View3DBase", "View2DSlice"]

from .simulation import MonteCarloPi3D
from .view3d import View3DBase, create_3d_view
from .view2d import View2DSlice
