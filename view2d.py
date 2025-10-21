"""
view2d.py

2D slice visualization using Matplotlib.
Shows a cross-section through the 3D data at a user-selected plane and position.
"""

import numpy as np
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure


class View2DSlice:
    """
    2D slice view showing a cross-section through the 3D Monte Carlo simulation.
    
    The slice is perpendicular to a chosen axis (X, Y, or Z) at a specific position.
    Points within a thickness slab are projected onto the 2D plane.
    """
    
    def __init__(self, parent: QWidget):
        """
        Initialize the 2D slice view.
        
        Args:
            parent: Parent widget to contain the 2D view
        """
        self.parent = parent
        self.canvas: Optional[FigureCanvasQTAgg] = None
        self.ax = None
        self.toolbar = None
        
        # Plot elements
        self.inside_scatter = None
        self.outside_scatter = None
        self.circle_patch = None
        self.square_patch = None
        
        # Slice parameters
        self.axis = 0  # 0=X, 1=Y, 2=Z
        self.slice_pos = 0.0
        self.thickness = 0.02
        
        self.setup_view()
    
    def setup_view(self):
        """Set up the Matplotlib figure, axes, and toolbar."""
        # Create layout
        layout = QVBoxLayout(self.parent)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create figure and canvas
        fig = Figure(figsize=(6, 6), facecolor='#1e1e1e')
        self.canvas = FigureCanvasQTAgg(fig)
        
        # Create toolbar
        self.toolbar = NavigationToolbar2QT(self.canvas, self.parent)
        
        # Add to layout
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Create axes
        self.ax = fig.add_subplot(111, facecolor='#1e1e1e')
        self.ax.set_aspect('equal')
        self.ax.set_xlim(-1.1, 1.1)
        self.ax.set_ylim(-1.1, 1.1)
        self.ax.grid(True, color='#444444', linestyle='--', linewidth=0.5, alpha=0.5)
        
        # Style axes
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        
        # Draw initial bounds
        self._draw_bounds()
        
        # Initialize scatter plots
        self.inside_scatter = self.ax.scatter([], [], c='green', s=10, alpha=0.8, label='Inside', zorder=3)
        self.outside_scatter = self.ax.scatter([], [], c='red', s=10, alpha=0.6, label='Outside', zorder=2)
        
        self.ax.legend(loc='upper right', facecolor='#2e2e2e', edgecolor='white', labelcolor='white')
        
        self.canvas.draw()
    
    def _draw_bounds(self):
        """Draw the square bounds and circle cross-section."""
        # Remove old patches
        if self.square_patch is not None:
            self.square_patch.remove()
        if self.circle_patch is not None:
            self.circle_patch.remove()
        
        # Draw square bounds [-1, 1]²
        from matplotlib.patches import Rectangle, Circle
        self.square_patch = Rectangle(
            (-1, -1), 2, 2,
            fill=False,
            edgecolor='white',
            linewidth=2,
            zorder=1
        )
        self.ax.add_patch(self.square_patch)
        
        # Calculate circle radius
        # Always create a circle patch so the artist exists; hide it when r<=0
        r_squared = 1.0 - self.slice_pos ** 2
        r = 0.0
        if r_squared > 0:
            r = float(np.sqrt(r_squared))

        # Create circle patch (may be radius 0) and control visibility
        self.circle_patch = Circle(
            (0, 0), r,
            fill=False,
            edgecolor='cyan',
            linewidth=2,
            linestyle='--',
            alpha=0.7,
            zorder=1
        )
        self.circle_patch.set_visible(r > 0.0)
        self.ax.add_patch(self.circle_patch)
        
        # Update title and labels
        axis_names = ['X', 'Y', 'Z']
        axis_labels = [['Y', 'Z'], ['X', 'Z'], ['X', 'Y']]
        
        self.ax.set_xlabel(axis_labels[self.axis][0], color='white', fontsize=12)
        self.ax.set_ylabel(axis_labels[self.axis][1], color='white', fontsize=12)
        
        title = f'Slice {axis_names[self.axis]}={self.slice_pos:.2f} (Δ={self.thickness:.3f})'
        if r_squared > 0:
            title += f' — r={np.sqrt(r_squared):.3f}'
        self.ax.set_title(title, color='white', fontsize=14, pad=10)
    
    def set_slice_params(self, axis: int, slice_pos: float, thickness: float):
        """
        Update slice parameters and redraw bounds.
        
        Args:
            axis: Axis perpendicular to slice (0=X, 1=Y, 2=Z)
            slice_pos: Position along chosen axis
            thickness: Thickness of slice slab
        """
        self.axis = axis
        self.slice_pos = slice_pos
        self.thickness = thickness
        self._draw_bounds()
        self.canvas.draw_idle()
    
    def update_slice_data(
        self,
        all_points: np.ndarray,
        all_masks: np.ndarray
    ):
        """
        Update the slice view with filtered points.
        
        Args:
            all_points: All generated points, shape (n, 3)
            all_masks: Inside/outside masks for all points, shape (n,)
        """
        # Update circle radius/visibility based on current slice_pos
        r_squared = 1.0 - self.slice_pos ** 2
        if self.circle_patch is not None:
            if r_squared > 0:
                r = float(np.sqrt(r_squared))
                self.circle_patch.set_radius(r)
                self.circle_patch.set_visible(True)
            else:
                # Tangent or outside: hide circle
                self.circle_patch.set_radius(0.0)
                self.circle_patch.set_visible(False)
        
        # Filter points in slice slab
        axis_coords = all_points[:, self.axis]
        in_slab = np.abs(axis_coords - self.slice_pos) <= (self.thickness / 2.0)
        
        if not np.any(in_slab):
            # No points in slice - set empty offsets but keep artists alive
            self.inside_scatter.set_offsets(np.empty((0, 2)))
            self.outside_scatter.set_offsets(np.empty((0, 2)))
            # Update title to show current slice parameters even when empty
            axis_names = ['X', 'Y', 'Z']
            title = f'Slice {axis_names[self.axis]}={self.slice_pos:.2f} (Δ={self.thickness:.3f})'
            self.ax.set_title(title, color='white', fontsize=14, pad=10)
            self.canvas.draw_idle()
            return
        
        # Get points in slice
        slice_points_3d = all_points[in_slab]
        slice_masks = all_masks[in_slab]
        
        # Project to 2D plane (drop the axis coordinate)
        other_axes = [i for i in range(3) if i != self.axis]
        slice_points_2d = slice_points_3d[:, other_axes]
        
        # Separate inside and outside
        inside_2d = slice_points_2d[slice_masks]
        outside_2d = slice_points_2d[~slice_masks]
        
        # Update scatter plots
        if len(inside_2d) > 0:
            self.inside_scatter.set_offsets(inside_2d)
        else:
            self.inside_scatter.set_offsets(np.empty((0, 2)))
        
        if len(outside_2d) > 0:
            self.outside_scatter.set_offsets(outside_2d)
        else:
            self.outside_scatter.set_offsets(np.empty((0, 2)))
        
        # Update title to include current radius if available
        axis_names = ['X', 'Y', 'Z']
        title = f'Slice {axis_names[self.axis]}={self.slice_pos:.2f} (Δ={self.thickness:.3f})'
        if r_squared > 0:
            title += f' — r={np.sqrt(r_squared):.3f}'
        self.ax.set_title(title, color='white', fontsize=14, pad=10)

        self.canvas.draw_idle()
    
    def clear(self):
        """Clear all points from the slice view."""
        self.inside_scatter.set_offsets(np.empty((0, 2)))
        self.outside_scatter.set_offsets(np.empty((0, 2)))
        # Hide circle on clear (keeps artist but invisible)
        if self.circle_patch is not None:
            self.circle_patch.set_visible(False)
        # Keep axes and bounds intact
        self.canvas.draw()
    
    def screenshot(self, filename: str):
        """
        Save a screenshot of the current slice view.
        
        Args:
            filename: Output filename for the screenshot
        """
        self.canvas.figure.savefig(
            filename,
            dpi=150,
            facecolor='#1e1e1e',
            bbox_inches='tight'
        )
