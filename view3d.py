"""
view3d.py

3D visualization using PyVista (primary) with Matplotlib fallback.
Displays the cube bounds, unit sphere, and point clouds colored by inside/outside.
"""

import numpy as np
from typing import Optional, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox

# Try to import PyVista
PYVISTA_AVAILABLE = False
try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
    PYVISTA_AVAILABLE = True
except ImportError:
    pass

# Matplotlib fallback
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D


class View3DBase:
    """Base class for 3D view implementations."""
    
    def __init__(self, parent: QWidget):
        """Initialize the 3D view."""
        self.parent = parent
        self.setup_view()
    
    def setup_view(self):
        """Set up the 3D visualization."""
        raise NotImplementedError
    
    def add_points(self, points: np.ndarray, inside_mask: np.ndarray):
        """
        Add a batch of points to the visualization.
        
        Args:
            points: Array of shape (n, 3) with point coordinates
            inside_mask: Boolean array of shape (n,) indicating inside/outside
        """
        raise NotImplementedError
    
    def clear_points(self):
        """Clear all points from the visualization."""
        raise NotImplementedError
    
    def reset_camera(self):
        """Reset camera to default view."""
        raise NotImplementedError


class View3DPyVista(View3DBase):
    """3D view using PyVista for high-performance rendering."""
    
    def __init__(self, parent: QWidget):
        """Initialize PyVista 3D view."""
        self.plotter: Optional[QtInteractor] = None
        self.inside_actor = None
        self.outside_actor = None
        self.slice_plane_actor = None
        self.slice_circle_actor = None
        self.inside_points = []
        self.outside_points = []
        super().__init__(parent)
    
    def setup_view(self):
        """Set up PyVista plotter with cube, sphere, and point clouds."""
        # Create layout for parent widget
        layout = QVBoxLayout(self.parent)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create PyVista QtInteractor
        self.plotter = QtInteractor(self.parent)
        layout.addWidget(self.plotter.interactor)
        
        # Set background
        self.plotter.set_background('#1e1e1e')
        
        # Add wireframe cube [-1, 1]³
        cube = pv.Cube(bounds=(-1, 1, -1, 1, -1, 1))
        self.plotter.add_mesh(
            cube.extract_all_edges(),
            color='white',
            line_width=2,
            label='Cube'
        )
        
        # Add semi-transparent unit sphere
        sphere = pv.Sphere(radius=1.0, theta_resolution=50, phi_resolution=50)
        self.plotter.add_mesh(
            sphere,
            color='cyan',
            opacity=0.05,
            show_edges=False,
            label='Unit Sphere'
        )
        
        # Set up axes
        self.plotter.show_axes()
        
        # Set initial camera
        self.reset_camera()
        
        # Enable anti-aliasing
        self.plotter.enable_anti_aliasing()

    def set_slice_plane(self, axis: int, pos: float, thickness: float = 0.0):
        """Add or update a translucent plane showing the current 2D slice.

        axis: 0->X, 1->Y, 2->Z
        pos: position along axis in [-1, 1]
        thickness: currently unused (kept for API compatibility)
        """
        # Remove old plane if present
        if getattr(self, 'slice_plane_actor', None) is not None:
            try:
                self.plotter.remove_actor(self.slice_plane_actor)
            except Exception:
                pass
            self.slice_plane_actor = None

        # Create plane centered at the requested position spanning the cube [-1,1]^2
        center = [0.0, 0.0, 0.0]
        normal = [0.0, 0.0, 0.0]
        if axis == 0:
            center = [pos, 0.0, 0.0]
            normal = [1.0, 0.0, 0.0]
        elif axis == 1:
            center = [0.0, pos, 0.0]
            normal = [0.0, 1.0, 0.0]
        else:
            center = [0.0, 0.0, pos]
            normal = [0.0, 0.0, 1.0]

        try:
            plane = pv.Plane(center=tuple(center), direction=tuple(normal), i_size=2.0, j_size=2.0)
            self.slice_plane_actor = self.plotter.add_mesh(
                plane,
                color='lightblue',
                opacity=0.25,
                show_edges=False,
                pickable=False
            )
        except Exception:
            # Non-fatal: if plane creation fails, ignore
            self.slice_plane_actor = None
        # Also draw circle representing intersection of sphere and plane
        # radius r = sqrt(max(0, 1 - pos^2))
        try:
            r_sq = 1.0 - float(pos) ** 2
            if r_sq > 0:
                r = float(np.sqrt(r_sq))
                # create circle points
                theta = np.linspace(0.0, 2.0 * np.pi, 128, endpoint=False)
                if axis == 0:
                    pts = np.column_stack((np.full_like(theta, pos), r * np.cos(theta), r * np.sin(theta)))
                elif axis == 1:
                    pts = np.column_stack((r * np.cos(theta), np.full_like(theta, pos), r * np.sin(theta)))
                else:
                    pts = np.column_stack((r * np.cos(theta), r * np.sin(theta), np.full_like(theta, pos)))

                # create polyline connectivity
                n = len(pts)
                lines = np.empty(n + 1, dtype=np.int_)
                lines[0] = n
                lines[1:] = np.arange(n)
                pd = pv.PolyData(pts)
                pd.lines = lines
                # remove previous circle
                if getattr(self, 'slice_circle_actor', None) is not None:
                    try:
                        self.plotter.remove_actor(self.slice_circle_actor)
                    except Exception:
                        pass
                    self.slice_circle_actor = None

                self.slice_circle_actor = self.plotter.add_mesh(pd, color='deepskyblue', line_width=2, render_lines_as_tubes=False)
        except Exception:
            pass
    
    def add_points(self, points: np.ndarray, inside_mask: np.ndarray):
        """
        Add points to the visualization.
        
        Args:
            points: Array of shape (n, 3) with point coordinates
            inside_mask: Boolean array of shape (n,) indicating inside/outside
        """
        # Separate inside and outside points
        inside_pts = points[inside_mask]
        outside_pts = points[~inside_mask]
        
        # Store points
        if len(inside_pts) > 0:
            self.inside_points.append(inside_pts)
        if len(outside_pts) > 0:
            self.outside_points.append(outside_pts)
        
        # Remove old actors
        if self.inside_actor is not None:
            self.plotter.remove_actor(self.inside_actor)
        if self.outside_actor is not None:
            self.plotter.remove_actor(self.outside_actor)
        
        # Create new point clouds
        if self.inside_points:
            all_inside = np.vstack(self.inside_points)
            inside_cloud = pv.PolyData(all_inside)
            self.inside_actor = self.plotter.add_points(
                inside_cloud,
                color='green',
                point_size=5,
                render_points_as_spheres=True,
                opacity=0.8
            )
        
        if self.outside_points:
            all_outside = np.vstack(self.outside_points)
            outside_cloud = pv.PolyData(all_outside)
            self.outside_actor = self.plotter.add_points(
                outside_cloud,
                color='red',
                point_size=5,
                render_points_as_spheres=True,
                opacity=0.25
            )
    
    def clear_points(self):
        """Clear all points from the visualization."""
        if self.inside_actor is not None:
            self.plotter.remove_actor(self.inside_actor)
            self.inside_actor = None
        if self.outside_actor is not None:
            self.plotter.remove_actor(self.outside_actor)
            self.outside_actor = None
        if getattr(self, 'slice_circle_actor', None) is not None:
            try:
                self.plotter.remove_actor(self.slice_circle_actor)
            except Exception:
                pass
            self.slice_circle_actor = None
        
        self.inside_points.clear()
        self.outside_points.clear()
    
    def reset_camera(self):
        """Reset camera to default isometric view."""
        # Zoomed out a bit so the scene fits comfortably
        self.plotter.camera_position = [
            (5, 5, 5),  # Camera position (farther out)
            (0, 0, 0),  # Focal point
            (0, 0, 1)   # View up
        ]
    def screenshot(self, filename: str):
        """Save a screenshot of the current view."""
        self.plotter.screenshot(filename, transparent_background=False)


class View3DMatplotlib(View3DBase):
    """3D view using Matplotlib as fallback."""
    
    def __init__(self, parent: QWidget):
        """Initialize Matplotlib 3D view."""
        self.canvas: Optional[FigureCanvasQTAgg] = None
        self.ax: Optional[Axes3D] = None
        self.inside_scatter = None
        self.outside_scatter = None
        self.inside_points = []
        self.outside_points = []
        self.max_display_points = 100000  # Limit for performance
        self.slice_plane = None
        self.slice_circle = None
        super().__init__(parent)
    
    def setup_view(self):
        """Set up Matplotlib 3D axes with cube, sphere, and scatter plots."""
        # Create layout for parent widget
        layout = QVBoxLayout(self.parent)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create figure and canvas
        fig = Figure(figsize=(8, 8), facecolor='#1e1e1e')
        self.canvas = FigureCanvasQTAgg(fig)
        layout.addWidget(self.canvas)
        
        # Create 3D axes
        self.ax = fig.add_subplot(111, projection='3d', facecolor='#1e1e1e')
        
        # Set limits and labels
        self.ax.set_xlim(-1, 1)
        self.ax.set_ylim(-1, 1)
        self.ax.set_zlim(-1, 1)
        self.ax.set_xlabel('X', color='white')
        self.ax.set_ylabel('Y', color='white')
        self.ax.set_zlabel('Z', color='white')
        self.ax.set_title('3D Monte Carlo (Matplotlib Fallback)', color='white', pad=20)
        
        # Equal aspect ratio
        self.ax.set_box_aspect([1, 1, 1])
        
        # Style axes
        self.ax.tick_params(colors='white')
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        self.ax.xaxis.pane.set_edgecolor('#444444')
        self.ax.yaxis.pane.set_edgecolor('#444444')
        self.ax.zaxis.pane.set_edgecolor('#444444')
        self.ax.grid(color='#444444', linestyle='--', linewidth=0.5)
        
        # Draw cube wireframe
        self._draw_cube()
        
        # Draw sphere wireframe
        self._draw_sphere()
        
        # Initialize empty scatter plots
        self.inside_scatter = self.ax.scatter([], [], [], c='green', s=10, alpha=0.8, depthshade=True)
        self.outside_scatter = self.ax.scatter([], [], [], c='red', s=10, alpha=0.25, depthshade=True)

        self.canvas.draw()

    def set_slice_plane(self, axis: int, pos: float, thickness: float = 0.0):
        """Draw or update a translucent plane in the Matplotlib 3D axes representing the slice."""
        # Remove existing plane collection
        if self.slice_plane is not None:
            try:
                for coll in self.slice_plane:
                    coll.remove()
            except Exception:
                pass
            self.slice_plane = None

        # Generate a square plane in the plane perpendicular to the axis
        grid = np.linspace(-1.0, 1.0, 2)
        X, Y = np.meshgrid(grid, grid)

        if axis == 0:
            # Plane x = pos
            X3 = np.full_like(X, pos)
            Y3 = X
            Z3 = Y
        elif axis == 1:
            # Plane y = pos
            X3 = X
            Y3 = np.full_like(X, pos)
            Z3 = Y
        else:
            # Plane z = pos
            X3 = X
            Y3 = Y
            Z3 = np.full_like(X, pos)

        # Draw translucent surface
        try:
            coll = self.ax.plot_surface(X3, Y3, Z3, color='lightblue', alpha=0.25, linewidth=0, shade=False)
            self.slice_plane = [coll]
            self.canvas.draw_idle()
        except Exception:
            self.slice_plane = None
        # Draw circle where sphere intersects plane
        try:
            r_sq = 1.0 - float(pos) ** 2
            if r_sq > 0:
                r = float(np.sqrt(r_sq))
                theta = np.linspace(0.0, 2.0 * np.pi, 128, endpoint=False)
                if axis == 0:
                    Xc = np.full_like(theta, pos)
                    Yc = r * np.cos(theta)
                    Zc = r * np.sin(theta)
                elif axis == 1:
                    Xc = r * np.cos(theta)
                    Yc = np.full_like(theta, pos)
                    Zc = r * np.sin(theta)
                else:
                    Xc = r * np.cos(theta)
                    Yc = r * np.sin(theta)
                    Zc = np.full_like(theta, pos)

                # Plot as a 3D line on the axes
                try:
                    # remove existing if present
                    if hasattr(self, 'slice_circle') and self.slice_circle is not None:
                        for line in self.slice_circle:
                            try:
                                line.remove()
                            except Exception:
                                pass
                    self.slice_circle = [self.ax.plot(Xc, Yc, Zc, color='deepskyblue', linewidth=2, linestyle='-')]
                    self.canvas.draw_idle()
                except Exception:
                    pass
        except Exception:
            pass
    
    def _draw_cube(self):
        """Draw wireframe cube."""
        # Define cube edges
        r = [-1, 1]
        for s, e in [(0, 1)]:
            for i in r:
                for j in r:
                    self.ax.plot([r[s], r[e]], [i, i], [j, j], 'w-', linewidth=1)
                    self.ax.plot([i, i], [r[s], r[e]], [j, j], 'w-', linewidth=1)
                    self.ax.plot([i, i], [j, j], [r[s], r[e]], 'w-', linewidth=1)
    
    def _draw_sphere(self):
        """Draw wireframe sphere."""
        u = np.linspace(0, 2 * np.pi, 30)
        v = np.linspace(0, np.pi, 20)
        x = np.outer(np.cos(u), np.sin(v))
        y = np.outer(np.sin(u), np.sin(v))
        z = np.outer(np.ones(np.size(u)), np.cos(v))
        
        self.ax.plot_wireframe(x, y, z, color='cyan', alpha=0.15, linewidth=0.5)
    
    def add_points(self, points: np.ndarray, inside_mask: np.ndarray):
        """
        Add points to the visualization (with display limit).
        
        Args:
            points: Array of shape (n, 3) with point coordinates
            inside_mask: Boolean array of shape (n,) indicating inside/outside
        """
        # Separate inside and outside points
        inside_pts = points[inside_mask]
        outside_pts = points[~inside_mask]
        
        # Store points (with limit)
        if len(inside_pts) > 0:
            self.inside_points.append(inside_pts)
        if len(outside_pts) > 0:
            self.outside_points.append(outside_pts)
        
        # Limit total points for performance
        all_inside = np.vstack(self.inside_points) if self.inside_points else np.empty((0, 3))
        all_outside = np.vstack(self.outside_points) if self.outside_points else np.empty((0, 3))
        
        # Sample if too many points
        if len(all_inside) > self.max_display_points // 2:
            indices = np.random.choice(len(all_inside), self.max_display_points // 2, replace=False)
            all_inside = all_inside[indices]
        if len(all_outside) > self.max_display_points // 2:
            indices = np.random.choice(len(all_outside), self.max_display_points // 2, replace=False)
            all_outside = all_outside[indices]
        
        # Update scatter plots
        if len(all_inside) > 0:
            self.inside_scatter._offsets3d = (all_inside[:, 0], all_inside[:, 1], all_inside[:, 2])
        
        if len(all_outside) > 0:
            self.outside_scatter._offsets3d = (all_outside[:, 0], all_outside[:, 1], all_outside[:, 2])
        
        self.canvas.draw_idle()
    
    def clear_points(self):
        """Clear all points from the visualization."""
        self.inside_points.clear()
        self.outside_points.clear()
        self.inside_scatter._offsets3d = ([], [], [])
        self.outside_scatter._offsets3d = ([], [], [])
        self.canvas.draw()
    
    def reset_camera(self):
        """Reset camera to default view."""
        self.ax.view_init(elev=30, azim=45)
        # Increase the virtual camera distance to appear slightly zoomed out
        try:
            self.ax.dist = 12
        except Exception:
            pass
        self.canvas.draw()
    
    def screenshot(self, filename: str):
        """Save a screenshot of the current view."""
        self.canvas.figure.savefig(filename, dpi=150, facecolor='#1e1e1e', bbox_inches='tight')


def create_3d_view(parent: QWidget) -> View3DBase:
    """
    Factory function to create appropriate 3D view.
    
    Args:
        parent: Parent widget to contain the 3D view
        
    Returns:
        View3DBase instance (PyVista or Matplotlib)
    """
    if PYVISTA_AVAILABLE:
        try:
            return View3DPyVista(parent)
        except Exception as e:
            print(f"PyVista initialization failed: {e}")
            print("Falling back to Matplotlib...")
    
    return View3DMatplotlib(parent)
