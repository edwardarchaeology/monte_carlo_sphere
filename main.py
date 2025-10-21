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
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QAbstractSpinBox,
    QGroupBox,
    QLabel,
    QTextEdit,
    QFormLayout,
)
from PySide6.QtGui import QFont
from PySide6.QtGui import QIcon
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap
from io import BytesIO
import matplotlib.pyplot as plt

# Local imports: these are project-local modules. When running from a PyInstaller-built
# executable or from other working directories, Python's import machinery may not find
# them. Use a guarded import that adds the project directory to sys.path as a fallback.
try:
    from simulation import MonteCarloPi3D
    from view3d import create_3d_view, View3DBase
    from view2d import View2DSlice
    from theme import apply_theme, DARK_THEME, LIGHT_THEME
except ModuleNotFoundError:
    # Robust fallback for frozen/executable environments (PyInstaller, onefile/onedir, etc.)
    candidates = []
    try:
        # Directory containing this source file (works when running from source)
        candidates.append(Path(__file__).resolve().parent)
    except Exception:
        pass
    try:
        # Directory containing the running executable/script (works when frozen)
        candidates.append(Path(sys.argv[0]).resolve().parent)
    except Exception:
        pass
    # PyInstaller sets sys._MEIPASS to the temporary extraction path for onefile mode
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        try:
            candidates.append(Path(meipass))
        except Exception:
            pass

    # Insert any unique candidate directories at front of sys.path
    for p in candidates:
        sp = str(p)
        if sp and sp not in sys.path:
            sys.path.insert(0, sp)

    # Retry imports; if these still fail we'll let the original exception propagate
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
        # Fix spinbox button hitboxes for better UX (small embedded +/- areas can be hard to click)
        try:
            self.fix_spinbox_buttons()
        except Exception:
            # Non-fatal if styling fails on a platform
            pass

        # Create a boxed Pi Estimates area (large, bold) and an About blurb
        try:
            # Pi estimates group
            pi_group = QGroupBox("Pi Estimates")
            pi_form = QFormLayout()
            bold = QFont()
            bold.setBold(True)

            self.pi3d_big = QLabel("—")
            self.pi3d_big.setFont(bold)
            self.err3d_big = QLabel("—")
            self.err3d_big.setFont(bold)
            self.pi2d_big = QLabel("—")
            self.pi2d_big.setFont(bold)
            self.err2d_big = QLabel("—")
            self.err2d_big.setFont(bold)

            pi_form.addRow("π (3D):", self.pi3d_big)
            pi_form.addRow("Error (3D):", self.err3d_big)
            pi_form.addRow("π (2D Slice):", self.pi2d_big)
            pi_form.addRow("Error (2D):", self.err2d_big)
            pi_group.setLayout(pi_form)

            # About blurb
            about_group = QGroupBox("About")
            # Prepare an about container: include rendered formulas if possible, and always include a plain-text explanation
            about_container = QLabel()
            try:
                # use a QWidget with vertical layout to assemble content
                from PySide6.QtWidgets import QWidget, QVBoxLayout
                about_container = QWidget()
                ac_layout = QVBoxLayout(about_container)
                ac_layout.setContentsMargins(6, 6, 6, 6)

                # Instead of large rendered formula images, show a formatted HTML about text
                desc = QTextEdit()
                desc.setReadOnly(True)
                desc.setFrameStyle(0)
                about_html = """
<h3>About — math &amp; slice π estimation</h3>
<h4>Overview</h4>
<p>This app estimates &pi; by Monte Carlo sampling inside the unit cube <code>[-1,1]^3</code> and testing whether points fall inside the unit sphere <code>x^2 + y^2 + z^2 &le; 1</code>. It also computes an independent 2D estimate of &pi; from points in a thin slab (a &quot;slice&quot;) centered on a plane <code>A = s</code> (A is X, Y or Z). The following explains the exact geometry and the estimators used.</p>

<h4>3D volume-based estimator (brief)</h4>
<p>We uniformly sample points in the cube. Let <code>N</code> be the total number of sampled points and <code>M</code> be the number inside the sphere.<br>
Volume of cube = 8. Volume of unit sphere = (4/3)&pi; · 1^3 = 4&pi;/3.<br>
The probability <code>p</code> of a random point landing inside the sphere is <code>p = V_sphere / V_cube = (4&pi;/3) / 8 = &pi; / 6</code>.<br>
So an unbiased estimator for &pi; is: <code>&circ;pi;^_3D = 6 · M / N</code>.</p>

<h4>Geometry of a slice</h4>
<p>Consider the plane <code>A = s</code> (|s| &le; 1) with axis A ∈ {x,y,z}. The intersection of the unit sphere with this plane is a circle of radius:</p>
<pre>r(s) = sqrt(1 - s^2)</pre>
<p>(If |s| &gt; 1 the plane misses the sphere; if |s| = 1 the circle degenerates to a point.)</p>

<h4>2D slice estimator — ideal plane</h4>
<p>If we could sample uniformly on the plane inside the square <code>[-1,1]^2</code>, the probability a point falls inside the circle would be:</p>
<pre>p_2D = π · r(s)^2 / 4</pre>
<p>Rearranging gives the ideal-2D estimator for &pi;:</p>
<pre>π^_2D,plane = 4 · (I / T) / r(s)^2</pre>
<p>where <code>T</code> = number of points sampled on the plane (inside the square) and <code>I</code> = number of those that lie inside the circle. Valid only when <code>r(s) &gt; 0</code>.</p>

<h4>Practical implementation: slab of finite thickness Δ</h4>
<p>In the app we select points that fall into a slab (thickness Δ) centered on s:</p>
<pre>slab = { (x,y,z) : |A - s| ≤ Δ/2 }</pre>
<p>Points in the slab are projected onto the plane and used for the 2D test. Using a slab increases sample count (reduces variance) but introduces bias because different slices inside the slab have different radii r(A).</p>

<h4>Using slab data to estimate π (practical estimator)</h4>
<p>Let <code>N_total</code> = total generated points, <code>T</code> = number that fell inside the slab, <code>I</code> = number of those that are inside the sphere. Project slab points onto the slice plane and treat them as 2D samples; the practical estimator is:</p>
<pre>π^_2D = 4 · (I / T) / r(s)^2</pre>
<p>with <code>r(s) = sqrt(1 - s^2)</code>. This assumes Δ small so r(A) variation inside the slab is negligible.</p>

<h4>Stability, bias, and variance — practical rules</h4>
<ul>
  <li><strong>Tangent / near-zero radius:</strong> when s ≈ ±1, r(s) → 0 — do not compute π2D if <code>r(s) &lt; r_min</code> (e.g., 1e-3) or if T is too small.</li>
  <li><strong>Minimum samples:</strong> if T &lt; T_min (e.g., 50–200) the 2D estimate is too noisy — display &quot;—&quot; instead.</li>
  <li><strong>Bias vs variance:</strong> increasing Δ increases T but biases the estimator. Keep Δ small (recommended 0.01–0.05). To reduce variance without bias, increase total N_total.</li>
</ul>

<h4>Approx expected slab count</h4>
<p>E[T] ≈ N_total · (Δ / 2). Example: N_total = 100,000 and Δ = 0.02 → expected T ≈ 1000.</p>

<h4>Example numeric calculation</h4>
<p>Suppose s = 0.3, so r ≈ 0.953939. Suppose T = 1000 and I = 785. Then I/T = 0.785 and:</p>
<pre>π^_2D ≈ 4 / r^2 · (I / T) ≈ 4 / 0.909 · 0.785 ≈ 3.45</pre>

<h4>Implementation suggestions</h4>
<ul>
  <li>Show sliceCount (T) and only display π2D when T ≥ T_min and r(s) ≥ r_min.</li>
  <li>Show approximate expected T = N_total · (Δ / 2).</li>
  <li>For a less-biased thicker slab compute a weighted correction integrating r(A) over the slab (more complex).</li>
</ul>

<h4>Key formulas summary</h4>
<pre>r(s) = sqrt(1 - s^2)
Ideal 2D estimator (plane): π = 4 · (I / T) / r^2
Expected slab samples: E[T] ≈ N_total · (Δ / 2)</pre>
"""
                desc.setHtml(about_html)
                ac_layout.addWidget(desc)
            except Exception:
                # Fallback: single QTextEdit
                about_container = QTextEdit()
                about_container.setReadOnly(True)
                about_container.setPlainText(
                    "This application estimates π using a 3D Monte Carlo method inside the unit sphere.\n\n"
                    "Controls and math info unavailable in this build."
                )

            about_layout = QFormLayout()
            about_layout.addRow(about_container)
            about_group.setLayout(about_layout)

            # Make left dock contents scrollable
            try:
                from PySide6.QtWidgets import QScrollArea
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                # move existing contents into scroll area
                inner = self.ui.dockWidgetContents
                scroll.setWidget(inner)
                # replace dock contents with the scroll area
                self.ui.controlDock.setWidget(scroll)
                dock_layout = inner.layout()
            except Exception:
                dock_layout = self.ui.dockWidgetContents.layout()
            try:
                stats_idx = dock_layout.indexOf(self.ui.statsGroup)
            except Exception:
                stats_idx = -1

            # Try to insert the About group into the right panel placeholder if present
            try:
                about_placeholder = getattr(self.ui, 'aboutPlaceholder', None)
                if about_placeholder is not None:
                    # Place the assembled about_container widget inside the placeholder layout
                    ph_layout = about_placeholder.layout()
                    ph_layout.addWidget(about_container)
                    # Insert pi_group into the dock above statsGroup
                    if stats_idx >= 0:
                        dock_layout.insertWidget(stats_idx, pi_group)
                    else:
                        dock_layout.addWidget(pi_group)
                else:
                    if stats_idx >= 0:
                        dock_layout.insertWidget(stats_idx, pi_group)
                        dock_layout.insertWidget(stats_idx + 1, about_group)
                    else:
                        dock_layout.addWidget(pi_group)
                        dock_layout.addWidget(about_group)
            except Exception:
                if stats_idx >= 0:
                    dock_layout.insertWidget(stats_idx, pi_group)
                    dock_layout.insertWidget(stats_idx + 1, about_group)
                else:
                    dock_layout.addWidget(pi_group)
                    dock_layout.addWidget(about_group)
        except Exception:
            pass
    
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
        # Update 3D slice plane visualization (if supported)
        try:
            if hasattr(self.view_3d, 'set_slice_plane'):
                self.view_3d.set_slice_plane(axis, slice_pos, thickness)
        except Exception:
            pass
    
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
            # Update small labels if they still exist in the UI
            lbl = getattr(self.ui, 'pi3DLabel', None)
            if lbl is not None:
                try:
                    lbl.setText(f"{pi_3d:.6f}")
                except Exception:
                    pass
            lbl = getattr(self.ui, 'err3DLabel', None)
            if lbl is not None:
                try:
                    lbl.setText(f"{err_3d:.6f}")
                except Exception:
                    pass
            # Update big pi labels
            try:
                self.pi3d_big.setText(f"{pi_3d:.6f}")
                self.err3d_big.setText(f"{err_3d:.6f}")
            except Exception:
                pass
        else:
            lbl = getattr(self.ui, 'pi3DLabel', None)
            if lbl is not None:
                lbl.setText("—")
            lbl = getattr(self.ui, 'err3DLabel', None)
            if lbl is not None:
                lbl.setText("—")
        
        # 2D slice statistics
        axis = self.ui.sliceAxisCombo.currentIndex()
        slice_pos = self.ui.slicePosSpin.value()
        thickness = self.ui.sliceThicknessSpin.value()
        
        total_slice, inside_slice, pi_2d, err_2d = self.simulation.compute_slice_stats(
            axis, slice_pos, thickness
        )
        
        self.ui.sliceCountLabel.setText(f"{total_slice:,}")
        
        if total_slice > 0 and (1.0 - slice_pos ** 2) > 0:
            lbl2 = getattr(self.ui, 'pi2DLabel', None)
            if lbl2 is not None:
                try:
                    lbl2.setText(f"{pi_2d:.5f}")
                except Exception:
                    pass
            lbl2e = getattr(self.ui, 'err2DLabel', None)
            if lbl2e is not None:
                try:
                    lbl2e.setText(f"{err_2d:.5f}")
                except Exception:
                    pass
            try:
                self.pi2d_big.setText(f"{pi_2d:.5f}")
                self.err2d_big.setText(f"{err_2d:.5f}")
            except Exception:
                pass
        else:
            lbl2 = getattr(self.ui, 'pi2DLabel', None)
            if lbl2 is not None:
                lbl2.setText("—")
            lbl2e = getattr(self.ui, 'err2DLabel', None)
            if lbl2e is not None:
                lbl2e.setText("—")
        
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

    def fix_spinbox_buttons(self):
        """Increase the clickable area of embedded +/- buttons on spinboxes.

        This applies a targeted QSS and ensures the widgets use PlusMinus symbols.
        """
        names = ("targetSpin", "batchSpin", "slicePosSpin", "sliceThicknessSpin")
        qss = """
QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    min-width: 18px;
    max-width: 30px;
    width: 24px;
}
QSpinBox, QDoubleSpinBox {
    padding-left: 6px;
    /* leave room on the right for the up/down buttons so they don't overlap the text */
    padding-right: 34px;
}
/* Ensure buttons are positioned at the right top / right bottom respectively */
QSpinBox::up-button { subcontrol-origin: padding; subcontrol-position: right top; }
QSpinBox::down-button { subcontrol-origin: padding; subcontrol-position: right bottom; }
QDoubleSpinBox::up-button { subcontrol-origin: padding; subcontrol-position: right top; }
QDoubleSpinBox::down-button { subcontrol-origin: padding; subcontrol-position: right bottom; }
"""

        for name in names:
            spin = getattr(self.ui, name, None)
            if spin is None:
                continue
            # Ensure plus/minus symbols (in case .ui didn't persist on some platforms)
            try:
                spin.setButtonSymbols(QAbstractSpinBox.PlusMinus)
            except Exception:
                pass
            # Apply QSS to expand clickable area without changing visual style much
            try:
                spin.setStyleSheet(qss)
            except Exception:
                pass
    
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
    # On Windows, set the AppUserModelID so the taskbar uses our icon and groups correctly.
    if sys.platform == "win32":
        try:
            import ctypes
            # Use a reverse-DNS style AppID for proper taskbar grouping; change to your org/app id if desired
            app_id = u"com.yourorg.montepi"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception:
            # Non-fatal if not available
            pass

    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Create application
    app = QApplication(sys.argv)
    # Set application-wide icon (use a .ico on Windows for best results)
    try:
        icon_path = Path(__file__).parent / "assets" / "app.ico"
        app_icon = QIcon(str(icon_path))
        if not app_icon.isNull():
            app.setWindowIcon(app_icon)
    except Exception:
        app_icon = None

    app.setApplicationName("Monte Carlo π 3D")
    app.setOrganizationName("MontePi")
    
    # Create and show main window
    window = MonteCarloApp()
    try:
        if 'app_icon' in locals() and app_icon is not None:
            window.setWindowIcon(app_icon)
    except Exception:
        pass
    window.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
