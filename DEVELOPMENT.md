# Development Guide

This guide is for developers who want to extend or modify the 3D Monte Carlo π application.

## Development Setup

### Prerequisites

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy
```

### IDE Setup (VS Code)

```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true
}
```

## Project Architecture

### Component Overview

```
┌─────────────────────────────────────────┐
│            main.py                      │
│       (MonteCarloApp)                   │
│  - Loads UI                             │
│  - Wires signals/slots                  │
│  - Manages update loop                  │
└────────┬─────────────────┬──────────────┘
         │                 │
         v                 v
┌────────────────┐  ┌─────────────────┐
│ simulation.py  │  │  theme.py       │
│ MonteCarloPi3D │  │  Stylesheets    │
└────────┬───────┘  └─────────────────┘
         │
    ┌────┴────┐
    v         v
┌─────────┐ ┌──────────┐
│view3d.py│ │view2d.py │
│3D Canvas│ │2D Slice  │
└─────────┘ └──────────┘
```

### Data Flow

```
User Input → Qt Signals → MonteCarloApp → Simulation
                    ↓
              Update Loop (QTimer)
                    ↓
         Generate Batch → Update Views
                    ↓
            Update Statistics
```

## Adding New Features

### Example 1: Add a New Slice Computation

**Goal**: Compute volume estimate from slice data

**Step 1**: Extend `simulation.py`

```python
def compute_slice_volume(self, axis: int, slice_pos: float,
                        thickness: float) -> float:
    """Estimate sphere volume from slice data."""
    total_slice, inside_slice, _, _ = self.compute_slice_stats(
        axis, slice_pos, thickness
    )
    if total_slice == 0:
        return 0.0

    # Volume of slab
    slab_volume = 4 * thickness  # [-1,1]² × thickness

    # Ratio estimate
    volume_estimate = 8.0 * (inside_slice / total_slice)
    return volume_estimate
```

**Step 2**: Add UI element in Qt Designer

- Add `QLabel` with objectName `volumeLabel`
- Place in statistics group

**Step 3**: Update `main.py`

```python
def update_statistics(self):
    # ... existing code ...

    # Add volume estimate
    volume = self.simulation.compute_slice_volume(
        axis, slice_pos, thickness
    )
    self.ui.volumeLabel.setText(f"{volume:.4f}")
```

### Example 2: Add Export to JSON

**Step 1**: Import json in `main.py`

```python
import json
```

**Step 2**: Add UI button in Qt Designer

- Add `QPushButton` with objectName `exportJSONButton`
- Text: "Export JSON"

**Step 3**: Wire signal in `main.py`

```python
def wire_signals(self):
    # ... existing code ...
    self.ui.exportJSONButton.clicked.connect(self.export_json)

@Slot()
def export_json(self):
    """Export simulation data to JSON."""
    if self.simulation.total == 0:
        QMessageBox.warning(self, "No Data", "No points to export.")
        return

    filename, _ = QFileDialog.getSaveFileName(
        self, "Export JSON", "", "JSON Files (*.json)"
    )
    if not filename:
        return

    data = {
        "total_points": self.simulation.total,
        "inside_points": self.simulation.inside,
        "pi_estimate": self.simulation.pi3d,
        "abs_error": self.simulation.abs_err3d,
        "seed": self.simulation.seed,
        "points": self.simulation.get_all_points().tolist()
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

    QMessageBox.information(
        self, "Success", f"Exported to {filename}"
    )
```

### Example 3: Add Background Generation (QThread)

**Step 1**: Create `worker.py`

```python
from PySide6.QtCore import QThread, Signal
import numpy as np

class GeneratorWorker(QThread):
    """Background thread for point generation."""

    batchReady = Signal(np.ndarray, np.ndarray)  # points, masks
    finished = Signal()

    def __init__(self, simulation, batch_size, target):
        super().__init__()
        self.simulation = simulation
        self.batch_size = batch_size
        self.target = target
        self.running = True

    def run(self):
        """Generate batches in background."""
        while self.running and self.simulation.total < self.target:
            remaining = self.target - self.simulation.total
            batch = min(self.batch_size, remaining)

            points, masks = self.simulation.next_batch(batch)
            self.batchReady.emit(points, masks)

        self.finished.emit()

    def stop(self):
        """Stop generation."""
        self.running = False
```

**Step 2**: Integrate in `main.py`

```python
from worker import GeneratorWorker

class MonteCarloApp(QMainWindow):
    def __init__(self):
        # ... existing code ...
        self.worker = None

    def start_simulation(self):
        """Start background generation."""
        if self.worker is None or not self.worker.isRunning():
            target = self.ui.targetSpin.value()
            batch = self.ui.batchSpin.value()

            self.worker = GeneratorWorker(
                self.simulation, batch, target
            )
            self.worker.batchReady.connect(self.on_batch_ready)
            self.worker.finished.connect(self.on_generation_complete)
            self.worker.start()

    @Slot(np.ndarray, np.ndarray)
    def on_batch_ready(self, points, masks):
        """Handle batch from worker thread."""
        self.view_3d.add_points(points, masks)
        self.update_statistics()
```

## Testing New Features

### Writing Tests

**Test file**: `tests/test_my_feature.py`

```python
import pytest
from simulation import MonteCarloPi3D

class TestMyFeature:
    def test_new_computation(self):
        """Test new computation method."""
        sim = MonteCarloPi3D()
        sim.reset(seed=42)
        sim.next_batch(1000)

        result = sim.my_new_method()

        assert result > 0
        assert result < 10  # reasonable bounds
```

**Run tests**:

```bash
pytest tests/test_my_feature.py -v
```

### Integration Testing

**Manual test checklist**:

- [ ] Feature works with UI controls
- [ ] No errors in console
- [ ] Updates display correctly
- [ ] Works with reset/pause/resume
- [ ] Export includes new data
- [ ] Theme toggle doesn't break UI

## Performance Optimization

### Profiling

**Profile simulation**:

```python
import cProfile
import pstats

sim = MonteCarloPi3D()
sim.reset(seed=42)

cProfile.run('sim.next_batch(1000000)', 'profile_stats')
stats = pstats.Stats('profile_stats')
stats.sort_stats('cumulative').print_stats(10)
```

**Profile GUI**:

```python
# In main.py update_loop
import time
start = time.perf_counter()
# ... update code ...
elapsed = time.perf_counter() - start
print(f"Update took {elapsed*1000:.2f}ms")
```

### Optimization Tips

1. **Vectorize operations**: Use NumPy instead of loops
2. **Batch processing**: Generate multiple points at once
3. **Limit GUI updates**: Cap update rate to 30-60 FPS
4. **Use PyVista**: Much faster than Matplotlib for 3D
5. **Profile first**: Don't optimize without measuring

## Debugging

### Common Issues

**Issue**: UI elements not found

```python
# Check if widget exists
if hasattr(self.ui, 'myWidget'):
    self.ui.myWidget.setText("Value")
else:
    print("ERROR: myWidget not found in UI")
```

**Issue**: Signals not firing

```python
# Debug signal connections
@Slot()
def my_slot(self):
    print("SLOT CALLED")  # Add debug print
    # ... rest of code ...
```

**Issue**: NumPy shape mismatch

```python
# Check array shapes
print(f"Points shape: {points.shape}")
print(f"Masks shape: {masks.shape}")
assert points.shape[0] == masks.shape[0]
```

### Debug Mode

**Enable verbose output**:

```python
# At top of main.py
DEBUG = True

def debug_print(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

# Use throughout code
debug_print(f"Generated {len(points)} points")
```

## Code Style

### Follow Project Conventions

```python
# Good: Type hints and docstrings
def compute_value(x: float, y: float) -> float:
    """
    Compute something from x and y.

    Args:
        x: First parameter
        y: Second parameter

    Returns:
        Computed value
    """
    return x * y


# Bad: No types or docs
def compute_value(x, y):
    return x * y
```

### Formatting

```bash
# Format code
black main.py simulation.py

# Check style
flake8 main.py --max-line-length=100

# Type checking
mypy main.py --ignore-missing-imports
```

## Building Distribution

### Create Executable (PyInstaller)

**Install PyInstaller**:

```bash
pip install pyinstaller
```

**Build**:

```bash
pyinstaller --onefile --windowed \
  --name "MonteCarloPi3D" \
  --icon=icon.ico \
  --add-data "ui;ui" \
  main.py
```

**Result**: `dist/MonteCarloPi3D.exe`

### Create Installer (Inno Setup)

**Script**: `installer.iss`

```inno
[Setup]
AppName=3D Monte Carlo Pi
AppVersion=1.0
DefaultDirName={pf}\MonteCarloPi3D
OutputDir=installer
OutputBaseFilename=MonteCarloPi3D_Setup

[Files]
Source: "dist\MonteCarloPi3D.exe"; DestDir: "{app}"
Source: "README.md"; DestDir: "{app}"

[Icons]
Name: "{commondesktop}\Monte Carlo Pi"; Filename: "{app}\MonteCarloPi3D.exe"
```

## Contributing

### Pull Request Process

1. **Fork and branch**

   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes**

   - Add code
   - Write tests
   - Update docs

3. **Test thoroughly**

   ```bash
   pytest tests/ -v
   python main.py  # Manual test
   ```

4. **Format and lint**

   ```bash
   black *.py
   flake8 *.py
   ```

5. **Commit and push**

   ```bash
   git add .
   git commit -m "Add feature: description"
   git push origin feature/my-feature
   ```

6. **Create PR** with description of changes

## Resources

### Documentation

- **Qt for Python**: https://doc.qt.io/qtforpython/
- **PyVista**: https://docs.pyvista.org/
- **Matplotlib**: https://matplotlib.org/stable/contents.html
- **NumPy**: https://numpy.org/doc/

### Learning

- Qt Designer tutorial: https://realpython.com/qt-designer-python/
- Monte Carlo methods: https://en.wikipedia.org/wiki/Monte_Carlo_method
- Python packaging: https://packaging.python.org/

## Contact & Support

For questions or issues:

1. Check `README.md` for common solutions
2. Run tests to verify setup
3. Review error messages carefully
4. Search Qt/PyVista documentation

---

**Happy coding!** 🚀
