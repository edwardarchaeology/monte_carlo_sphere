"""
simulation.py

Core Monte Carlo simulation logic for 3D π approximation.
Uses vectorized NumPy operations for efficient batch generation.
"""

import numpy as np
from typing import Optional, Tuple


class MonteCarloPi3D:
    """
    Monte Carlo simulation for approximating π using random points in a unit cube
    and checking if they fall inside a unit sphere.
    
    The cube is [-1, 1]³ with volume 8.
    The unit sphere is x² + y² + z² ≤ 1 with volume (4/3)π.
    
    The ratio of points inside to total points approximates the volume ratio:
        inside/total ≈ (4π/3) / 8 = π/6
        
    Therefore: π ≈ 6 * (inside/total)
    """
    
    def __init__(self):
        """Initialize the simulation with default parameters."""
        self._rng: Optional[np.random.Generator] = None
        self._seed: Optional[int] = None
        self._inside: int = 0
        self._total: int = 0
        self._all_points: list = []  # Store all generated points
        self._all_masks: list = []   # Store corresponding inside/outside masks
        
    def reset(self, seed: Optional[int] = None) -> None:
        """
        Reset the simulation to initial state.
        
        Args:
            seed: Random seed for reproducibility. If None, uses random state.
        """
        self._seed = seed
        self._rng = np.random.default_rng(seed)
        self._inside = 0
        self._total = 0
        self._all_points.clear()
        self._all_masks.clear()
        
    def next_batch(self, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate the next batch of k random points.
        
        Args:
            k: Number of points to generate in this batch.
            
        Returns:
            Tuple of (points, inside_mask) where:
                - points: ndarray of shape (k, 3) with coordinates in [-1, 1]³
                - inside_mask: boolean ndarray of shape (k,) where True means inside sphere
        """
        if self._rng is None:
            self.reset()
            
        # Generate k random points uniformly in [-1, 1]³
        points = self._rng.uniform(-1.0, 1.0, size=(k, 3))
        
        # Check if points are inside unit sphere: x² + y² + z² ≤ 1
        distances_squared = np.sum(points ** 2, axis=1)
        inside_mask = distances_squared <= 1.0
        
        # Update running totals
        inside_count = np.sum(inside_mask)
        self._inside += inside_count
        self._total += k
        
        # Store points and masks
        self._all_points.append(points)
        self._all_masks.append(inside_mask)
        
        return points, inside_mask
    
    @property
    def inside(self) -> int:
        """Number of points inside the sphere."""
        return self._inside
    
    @property
    def outside(self) -> int:
        """Number of points outside the sphere."""
        return self._total - self._inside
    
    @property
    def total(self) -> int:
        """Total number of points generated."""
        return self._total
    
    @property
    def pi3d(self) -> float:
        """
        Current 3D π estimate.
        
        Since inside/total ≈ (4π/3) / 8 = π/6, we have:
            π ≈ 6 * (inside/total)
        """
        if self._total == 0:
            return 0.0
        return 6.0 * self._inside / self._total
    
    @property
    def abs_err3d(self) -> float:
        """Absolute error from true π value."""
        return abs(self.pi3d - np.pi)
    
    @property
    def seed(self) -> Optional[int]:
        """Current random seed."""
        return self._seed
    
    def get_all_points(self) -> np.ndarray:
        """
        Get all generated points as a single array.
        
        Returns:
            ndarray of shape (total, 3) with all points.
        """
        if not self._all_points:
            return np.empty((0, 3))
        return np.vstack(self._all_points)
    
    def get_all_masks(self) -> np.ndarray:
        """
        Get all inside/outside masks as a single array.
        
        Returns:
            boolean ndarray of shape (total,) with all masks.
        """
        if not self._all_masks:
            return np.empty(0, dtype=bool)
        return np.concatenate(self._all_masks)
    
    def compute_slice_stats(
        self,
        axis: int,
        slice_pos: float,
        thickness: float
    ) -> Tuple[int, int, float, float]:
        """
        Compute statistics for a 2D slice through the data.
        
        Args:
            axis: Axis perpendicular to slice (0=X, 1=Y, 2=Z)
            slice_pos: Position of slice along chosen axis, in [-1, 1]
            thickness: Thickness of the slice slab (delta)
            
        Returns:
            Tuple of (total_in_slice, inside_in_slice, pi_2d, abs_err_2d):
                - total_in_slice: Number of points in the slice slab
                - inside_in_slice: Number of those points inside the circle
                - pi_2d: 2D π estimate from slice (or 0 if not computable)
                - abs_err_2d: Absolute error from true π (or 0 if not computable)
        """
        if self._total == 0:
            return 0, 0, 0.0, 0.0
        
        # Get all points and masks
        all_pts = self.get_all_points()
        all_masks = self.get_all_masks()
        
        # Compute circle radius at this slice position
        # r = sqrt(1 - s²) where s is the slice position
        r_squared = 1.0 - slice_pos ** 2
        
        if r_squared <= 0:
            # Slice is tangent or outside sphere
            return 0, 0, 0.0, 0.0
        
        r = np.sqrt(r_squared)
        
        # Filter points in the slice slab: |axis_coord - slice_pos| ≤ thickness/2
        axis_coords = all_pts[:, axis]
        in_slab = np.abs(axis_coords - slice_pos) <= (thickness / 2.0)
        
        total_in_slice = np.sum(in_slab)
        
        if total_in_slice == 0:
            return 0, 0, 0.0, 0.0
        
        # Get the two axes that define the slice plane
        other_axes = [i for i in range(3) if i != axis]
        slice_points = all_pts[in_slab][:, other_axes]
        
        # Check which slice points are inside the circle: x² + y² ≤ r²
        distances_squared_2d = np.sum(slice_points ** 2, axis=1)
        inside_in_slice_mask = distances_squared_2d <= r_squared
        inside_in_slice = np.sum(inside_in_slice_mask)
        
        # Compute 2D π estimate
        # The slice square has area 4 ([-1,1]²)
        # The slice circle has area π*r²
        # So: inside/total ≈ π*r² / 4
        # Therefore: π ≈ 4 * (inside/total) / r²
        pi_2d = 4.0 * inside_in_slice / (total_in_slice * r_squared)
        abs_err_2d = abs(pi_2d - np.pi)
        
        return total_in_slice, inside_in_slice, pi_2d, abs_err_2d
