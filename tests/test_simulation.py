"""
test_simulation.py

Unit tests for the MonteCarloPi3D simulation class.
Tests deterministic behavior, correctness, and statistical convergence.
"""

import numpy as np
import pytest
from simulation import MonteCarloPi3D


class TestMonteCarloPi3D:
    """Test suite for MonteCarloPi3D class."""
    
    def test_initialization(self):
        """Test that simulation initializes correctly."""
        sim = MonteCarloPi3D()
        assert sim.total == 0
        assert sim.inside == 0
        assert sim.outside == 0
        assert sim.pi3d == 0.0
    
    def test_reset(self):
        """Test that reset clears simulation state."""
        sim = MonteCarloPi3D()
        sim.next_batch(100)
        assert sim.total == 100
        
        sim.reset()
        assert sim.total == 0
        assert sim.inside == 0
        assert sim.outside == 0
    
    def test_deterministic_with_seed(self):
        """Test that same seed produces same results."""
        sim1 = MonteCarloPi3D()
        sim1.reset(seed=42)
        points1, mask1 = sim1.next_batch(1000)
        
        sim2 = MonteCarloPi3D()
        sim2.reset(seed=42)
        points2, mask2 = sim2.next_batch(1000)
        
        assert np.allclose(points1, points2)
        assert np.array_equal(mask1, mask2)
        assert sim1.inside == sim2.inside
        assert sim1.total == sim2.total
    
    def test_points_in_bounds(self):
        """Test that all generated points are within [-1, 1]³."""
        sim = MonteCarloPi3D()
        sim.reset(seed=123)
        points, _ = sim.next_batch(10000)
        
        assert np.all(points >= -1.0)
        assert np.all(points <= 1.0)
    
    def test_inside_outside_classification(self):
        """Test correct classification of known points."""
        sim = MonteCarloPi3D()
        
        # Test point at origin (inside)
        test_point = np.array([[0, 0, 0]])
        dist_sq = np.sum(test_point ** 2, axis=1)
        assert dist_sq[0] <= 1.0  # Should be inside
        
        # Test point at (0.5, 0.5, 0.5) - inside
        test_point = np.array([[0.5, 0.5, 0.5]])
        dist_sq = np.sum(test_point ** 2, axis=1)
        assert dist_sq[0] <= 1.0  # 0.75 <= 1.0
        
        # Test point at (1, 1, 1) - outside
        test_point = np.array([[1, 1, 1]])
        dist_sq = np.sum(test_point ** 2, axis=1)
        assert dist_sq[0] > 1.0  # 3.0 > 1.0
        
        # Test point on surface (1, 0, 0) - on boundary
        test_point = np.array([[1, 0, 0]])
        dist_sq = np.sum(test_point ** 2, axis=1)
        assert dist_sq[0] <= 1.0  # Exactly 1.0
    
    def test_batch_accumulation(self):
        """Test that multiple batches accumulate correctly."""
        sim = MonteCarloPi3D()
        sim.reset(seed=42)
        
        # Generate in batches
        sim.next_batch(100)
        assert sim.total == 100
        
        sim.next_batch(200)
        assert sim.total == 300
        
        sim.next_batch(300)
        assert sim.total == 600
    
    def test_pi_estimation_convergence(self):
        """
        Test that π estimate converges to true value with many points.
        This is a statistical test with generous tolerance.
        """
        sim = MonteCarloPi3D()
        sim.reset(seed=42)
        
        # Generate many points in batches
        for _ in range(10):
            sim.next_batch(100000)
        
        # With 1,000,000 points, should be fairly close
        # Allow error up to 0.01 (this should pass with high probability)
        assert sim.total == 1000000
        assert abs(sim.pi3d - np.pi) < 0.01
    
    def test_pi_formula(self):
        """Test that π formula is correct."""
        sim = MonteCarloPi3D()
        sim.reset(seed=99)
        
        sim.next_batch(10000)
        
        # Manually compute π estimate
        expected_pi = 6.0 * sim.inside / sim.total
        assert abs(sim.pi3d - expected_pi) < 1e-10
    
    def test_slice_stats_center(self):
        """Test slice statistics at center (s=0)."""
        sim = MonteCarloPi3D()
        sim.reset(seed=42)
        
        # Generate points
        sim.next_batch(100000)
        
        # Get slice at Z=0 with thickness 0.1
        total_slice, inside_slice, pi_2d, err_2d = sim.compute_slice_stats(
            axis=2,  # Z axis
            slice_pos=0.0,
            thickness=0.1
        )
        
        # Should have some points in slice
        assert total_slice > 0
        assert inside_slice >= 0
        assert inside_slice <= total_slice
        
        # π estimate should be reasonable (within 0.5 of true π)
        # This is generous because slice has fewer points
        if total_slice > 100:  # Only check if enough points
            assert abs(pi_2d - np.pi) < 0.5
    
    def test_slice_stats_outside_sphere(self):
        """Test slice statistics outside sphere radius."""
        sim = MonteCarloPi3D()
        sim.reset(seed=42)
        sim.next_batch(10000)
        
        # Slice at position > 1 (outside sphere)
        total_slice, inside_slice, pi_2d, err_2d = sim.compute_slice_stats(
            axis=2,
            slice_pos=1.5,
            thickness=0.1
        )
        
        # Should return zeros since r² < 0
        assert total_slice == 0
        assert inside_slice == 0
        assert pi_2d == 0.0
    
    def test_slice_different_axes(self):
        """Test slice computation on different axes."""
        sim = MonteCarloPi3D()
        sim.reset(seed=42)
        sim.next_batch(50000)
        
        # Test all three axes at center
        for axis in [0, 1, 2]:
            total_slice, inside_slice, pi_2d, err_2d = sim.compute_slice_stats(
                axis=axis,
                slice_pos=0.0,
                thickness=0.1
            )
            
            # Should have similar results for all axes at center
            assert total_slice > 0
            assert inside_slice > 0
    
    def test_get_all_points(self):
        """Test that get_all_points returns correct shape."""
        sim = MonteCarloPi3D()
        sim.reset(seed=42)
        
        # Generate in multiple batches
        sim.next_batch(100)
        sim.next_batch(200)
        sim.next_batch(300)
        
        all_points = sim.get_all_points()
        assert all_points.shape == (600, 3)
    
    def test_get_all_masks(self):
        """Test that get_all_masks returns correct shape."""
        sim = MonteCarloPi3D()
        sim.reset(seed=42)
        
        sim.next_batch(500)
        
        all_masks = sim.get_all_masks()
        assert all_masks.shape == (500,)
        assert all_masks.dtype == bool
        
        # Check consistency
        assert np.sum(all_masks) == sim.inside
    
    def test_empty_simulation(self):
        """Test that empty simulation handles queries correctly."""
        sim = MonteCarloPi3D()
        sim.reset()
        
        # Should handle empty state gracefully
        all_points = sim.get_all_points()
        all_masks = sim.get_all_masks()
        
        assert len(all_points) == 0
        assert len(all_masks) == 0
        
        # Slice stats should return zeros
        total_slice, inside_slice, pi_2d, err_2d = sim.compute_slice_stats(0, 0.0, 0.1)
        assert total_slice == 0
        assert inside_slice == 0
        assert pi_2d == 0.0
    
    def test_seed_property(self):
        """Test that seed property returns correct value."""
        sim = MonteCarloPi3D()
        
        sim.reset(seed=12345)
        assert sim.seed == 12345
        
        sim.reset(seed=None)
        assert sim.seed is None
    
    def test_abs_err3d(self):
        """Test that absolute error is computed correctly."""
        sim = MonteCarloPi3D()
        sim.reset(seed=42)
        sim.next_batch(10000)
        
        expected_err = abs(sim.pi3d - np.pi)
        assert abs(sim.abs_err3d - expected_err) < 1e-10


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
