"""
main.py

Main application entry point for the 3D Monte Carlo π approximation GUI.
Loads the UI, embeds visualization canvases, wires signals/slots, and manages the simulation loop.
"""

import sys
import os
import time
import csv
from pathlib import Path
from typing import Optional

import numpy as np
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtUiTools import QUiLoader

from simulation import MonteCarloPi3D
from view3d import create_3d_view, View3DBase
from view2d import View2DSlice
from theme import apply_theme, DARK_THEME, LIGHT_THEME


class MonteCarloApp(QMainWindow):
    """Main application window for 3D Monte Carlo π approximation."""
    
    def __init__(self):
        """Initialize the application."""
        super().__init__()
        
        # Simulation state
        self.simulation = MonteCarloPi3D()
        self.is_running = False
        self.start_time = 0.0
        self.elapsed_time = 0.0
        
        # FPS tracking (exponential moving average)
        self.last_update_time = 0.0
        self.fps = 0.0
        self.fps_alpha = 0.1  # EMA smoothing factor
        
        # Views
        self.view_3d: Optional[View3DBase] = None
        self.view_2d: Optional[View2DSlice] = None
        
        # Timer for update loop
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer_interval = 33  # ~30 FPS (milliseconds)
        
        # Load UI and set up views
        self.load_ui()
        self.setup_views()
        self.wire_signals()
        self.reset_simulation()
        
        # Apply initial theme
        self.apply_current_theme()
    
    def load_ui(self):
        """Load the UI from the .ui file."""
        ui_file = Path(__file__).parent / "ui" / "main_window.ui"
        
        loader = QUiLoader()
        ui_widget = loader.load(str(ui_file), self)
        
        # Set as central widget and copy attributes
        self.setCentralWidget(ui_widget.centralwidget)
        self.setMenuBar(ui_widget.menubar)
        self.setStatusBar(ui_widget.statusbar)
        
        # Add dock widget
        self.addDockWidget(Qt.LeftDockWidgetArea, ui_widget.controlDock)
        
        # Store references to UI elements
        self.ui = ui_widget
        
        # Window properties
        self.setWindowTitle("3D Monte Carlo π Approximation")
        self.resize(1400, 900)
    
    def setup_views(self):
        """Set up 3D and 2D visualization canvases."""
        # Get host widgets from UI
        plot3d_host = self.ui.plot3DHost
        plot2d_host = self.ui.plot2DHost
        
        # Create views
        self.view_3d = create_3d_view(plot3d_host)
        self.view_2d = View2DSlice(plot2d_host)
    
    def wire_signals(self):
        """Wire all UI signals to slots."""
        # Simulation controls
        self.ui.startButton.clicked.connect(self.start_simulation)
        self.ui.pauseButton.clicked.connect(self.pause_simulation)
        self.ui.stepButton.clicked.connect(self.step_simulation)
        self.ui.resetButton.clicked.connect(self.reset_simulation)
        
        # Target points synchronization
        self.ui.targetSpin.valueChanged.connect(self.on_target_spin_changed)
        self.ui.targetSlider.valueChanged.connect(self.on_target_slider_changed)
        
        # Seed controls
        self.ui.randomizeSeedButton.clicked.connect(self.randomize_seed)
        
        # Slice controls
        self.ui.sliceAxisCombo.currentIndexChanged.connect(self.on_slice_params_changed)
        self.ui.slicePosSpin.valueChanged.connect(self.on_slice_pos_spin_changed)
        self.ui.slicePosSlider.valueChanged.connect(self.on_slice_pos_slider_changed)
        self.ui.sliceThicknessSpin.valueChanged.connect(self.on_slice_params_changed)
        
        # Theme toggle
        self.ui.darkThemeCheck.stateChanged.connect(self.toggle_theme)
        
        # Export features
        self.ui.savePNGButton.clicked.connect(self.save_png)
        self.ui.exportCSVButton.clicked.connect(self.export_csv)
    
    @Slot()
    def start_simulation(self):
        """Start the simulation."""
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time() - self.elapsed_time
            self.last_update_time = time.time()
            self.timer.start(self.timer_interval)
            
            # Update button states
            self.ui.startButton.setEnabled(False)
            self.ui.pauseButton.setEnabled(True)
    
    @Slot()
    def pause_simulation(self):
        """Pause the simulation."""
        if self.is_running:
            self.is_running = False
            self.timer.stop()
            self.elapsed_time = time.time() - self.start_time
            
            # Update button states
            self.ui.startButton.setEnabled(True)
            self.ui.pauseButton.setEnabled(False)
    
    @Slot()
    def step_simulation(self):
        """Execute one batch step."""
        if not self.is_running:
            self.update_loop()
    
    @Slot()
    def reset_simulation(self):
        """Reset the simulation to initial state."""
        # Stop if running
        if self.is_running:
            self.pause_simulation()
        
        # Get seed
        try:
            seed = int(self.ui.seedEdit.text())
        except ValueError:
            seed = None
        
        # Reset simulation
        self.simulation.reset(seed)
        
        # Reset timing
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.fps = 0.0
        
        # Clear views
        self.view_3d.clear_points()
        self.view_2d.clear()
        
        # Update UI
        self.update_statistics()
        
        # Update button states
        self.ui.startButton.setEnabled(True)
        self.ui.pauseButton.setEnabled(False)
    
    @Slot()
    def update_loop(self):
        """Main update loop called by timer."""
        # Check if we've reached target
        target = self.ui.targetSpin.value()
        if self.simulation.total >= target:
            if self.is_running:
                self.pause_simulation()
            return
        
        # Get batch size
        batch_size = self.ui.batchSpin.value()
        
        # Limit batch to not exceed target
        remaining = target - self.simulation.total
        batch_size = min(batch_size, remaining)
        
        if batch_size <= 0:
            return
        
        # Generate batch
        points, inside_mask = self.simulation.next_batch(batch_size)
        
        # Update 3D view
        self.view_3d.add_points(points, inside_mask)
        
        # Update 2D slice view
        self.update_slice_view()
        
        # Update statistics
        self.update_statistics()
        
        # Update FPS
        self.update_fps()
    
    def update_slice_view(self):
        """Update the 2D slice view with current data."""
        # Get slice parameters
        axis = self.ui.sliceAxisCombo.currentIndex()
        slice_pos = self.ui.slicePosSpin.value()
        thickness = self.ui.sliceThicknessSpin.value()
        
        # Update slice view parameters
        self.view_2d.set_slice_params(axis, slice_pos, thickness)
        
        # Get all points and update slice
        all_points = self.simulation.get_all_points()
        all_masks = self.simulation.get_all_masks()
        self.view_2d.update_slice_data(all_points, all_masks)
    
    def update_statistics(self):
        """Update all statistics labels."""
        # Basic counts
        self.ui.totalLabel.setText(f"{self.simulation.total:,}")
        self.ui.insideLabel.setText(f"{self.simulation.inside:,}")
        self.ui.outsideLabel.setText(f"{self.simulation.outside:,}")
        
        # 3D π estimate
        if self.simulation.total > 0:
            pi_3d = self.simulation.pi3d
            err_3d = self.simulation.abs_err3d
            self.ui.pi3DLabel.setText(f"{pi_3d:.6f}")
            self.ui.err3DLabel.setText(f"{err_3d:.6f}")
        else:
            self.ui.pi3DLabel.setText("—")
            self.ui.err3DLabel.setText("—")
        
        # 2D slice statistics
        axis = self.ui.sliceAxisCombo.currentIndex()
        slice_pos = self.ui.slicePosSpin.value()
        thickness = self.ui.sliceThicknessSpin.value()
        
        total_slice, inside_slice, pi_2d, err_2d = self.simulation.compute_slice_stats(
            axis, slice_pos, thickness
        )
        
        self.ui.sliceCountLabel.setText(f"{total_slice:,}")
        
        if total_slice > 0 and (1.0 - slice_pos ** 2) > 0:
            self.ui.pi2DLabel.setText(f"{pi_2d:.5f}")
            self.ui.err2DLabel.setText(f"{err_2d:.5f}")
        else:
            self.ui.pi2DLabel.setText("—")
            self.ui.err2DLabel.setText("—")
        
        # Update elapsed time
        if self.is_running:
            self.elapsed_time = time.time() - self.start_time
        self.ui.elapsedLabel.setText(f"{self.elapsed_time:.1f}s")
        
        # Update window title with progress
        if self.simulation.total > 0:
            target = self.ui.targetSpin.value()
            progress = 100.0 * self.simulation.total / target
            pi_3d = self.simulation.pi3d
            err_3d = self.simulation.abs_err3d
            self.setWindowTitle(
                f"3D Monte Carlo π — {self.simulation.total:,}/{target:,} ({progress:.1f}%) — "
                f"π₃D ≈ {pi_3d:.6f} (err {err_3d:.6f})"
            )
    
    def update_fps(self):
        """Update FPS counter using exponential moving average."""
        current_time = time.time()
        if self.last_update_time > 0:
            delta = current_time - self.last_update_time
            if delta > 0:
                instant_fps = 1.0 / delta
                # Exponential moving average
                self.fps = self.fps_alpha * instant_fps + (1 - self.fps_alpha) * self.fps
        self.last_update_time = current_time
        self.ui.fpsLabel.setText(f"{self.fps:.1f}")
    
    @Slot(int)
    def on_target_spin_changed(self, value: int):
        """Handle target spin box change."""
        # Update slider (but cap at slider max)
        slider_max = self.ui.targetSlider.maximum()
        self.ui.targetSlider.blockSignals(True)
        self.ui.targetSlider.setValue(min(value, slider_max))
        self.ui.targetSlider.blockSignals(False)
    
    @Slot(int)
    def on_target_slider_changed(self, value: int):
        """Handle target slider change."""
        # Update spin box
        self.ui.targetSpin.blockSignals(True)
        self.ui.targetSpin.setValue(value)
        self.ui.targetSpin.blockSignals(False)
    
    @Slot()
    def randomize_seed(self):
        """Generate a random seed."""
        seed = np.random.randint(0, 1000000)
        self.ui.seedEdit.setText(str(seed))
    
    @Slot()
    def on_slice_params_changed(self):
        """Handle slice parameter changes."""
        if self.simulation.total > 0:
            self.update_slice_view()
            self.update_statistics()
    
    @Slot(float)
    def on_slice_pos_spin_changed(self, value: float):
        """Handle slice position spin box change."""
        # Update slider
        slider_value = int(value * 100)
        self.ui.slicePosSlider.blockSignals(True)
        self.ui.slicePosSlider.setValue(slider_value)
        self.ui.slicePosSlider.blockSignals(False)
        
        self.on_slice_params_changed()
    
    @Slot(int)
    def on_slice_pos_slider_changed(self, value: int):
        """Handle slice position slider change."""
        # Update spin box
        spin_value = value / 100.0
        self.ui.slicePosSpin.blockSignals(True)
        self.ui.slicePosSpin.setValue(spin_value)
        self.ui.slicePosSpin.blockSignals(False)
        
        self.on_slice_params_changed()
    
    @Slot()
    def toggle_theme(self):
        """Toggle between dark and light theme."""
        self.apply_current_theme()
    
    def apply_current_theme(self):
        """Apply the current theme based on checkbox state."""
        dark = self.ui.darkThemeCheck.isChecked()
        apply_theme(QApplication.instance(), dark)
    
    @Slot()
    def save_png(self):
        """Save 3D and 2D views as PNG images."""
        # Get save location
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save PNG",
            "",
            "PNG Images (*.png)"
        )
        
        if not filename:
            return
        
        try:
            # Save 3D view
            base = Path(filename).stem
            parent = Path(filename).parent
            suffix = Path(filename).suffix
            
            view3d_file = parent / f"{base}_3D{suffix}"
            view2d_file = parent / f"{base}_2D{suffix}"
            
            self.view_3d.screenshot(str(view3d_file))
            self.view_2d.screenshot(str(view2d_file))
            
            QMessageBox.information(
                self,
                "Save Successful",
                f"Saved screenshots:\n{view3d_file}\n{view2d_file}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save PNG: {str(e)}"
            )
    
    @Slot()
    def export_csv(self):
        """Export all points to CSV file."""
        if self.simulation.total == 0:
            QMessageBox.warning(
                self,
                "No Data",
                "No points to export. Run the simulation first."
            )
            return
        
        # Get save location
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            "",
            "CSV Files (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            # Get all points and masks
            all_points = self.simulation.get_all_points()
            all_masks = self.simulation.get_all_masks()
            
            # Write CSV
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['x', 'y', 'z', 'in_sphere'])
                
                for i in range(len(all_points)):
                    x, y, z = all_points[i]
                    in_sphere = int(all_masks[i])
                    writer.writerow([x, y, z, in_sphere])
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(all_points):,} points to:\n{filename}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export CSV: {str(e)}"
            )


def main():
    """Application entry point."""
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Monte Carlo π 3D")
    app.setOrganizationName("MontePi")
    
    # Create and show main window
    window = MonteCarloApp()
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
