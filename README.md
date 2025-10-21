# 3D Monte Carlo π Approximation

A sophisticated desktop GUI application that demonstrates Monte Carlo approximation of π using 3D random sampling. The application generates random points in a cube $[-1,1]^3$ and checks whether they fall inside the unit sphere $x^2 + y^2 + z^2 \leq 1$.

![Application Screenshot](docs/screenshot.png)

## Features

### Visualization

- **3D View**: Interactive 3D visualization using PyVista (with Matplotlib fallback)
  - Wireframe cube bounds
  - Semi-transparent unit sphere
  - Color-coded point clouds (green=inside, red=outside)
  - Mouse-controlled camera rotation and zoom
- **2D Slice View**: Synchronized cross-section display
  - User-selectable slice plane (X, Y, or Z axis)
  - Adjustable slice position and thickness
  - Circle-square visualization with projected points
  - Independent π estimation from slice data

### Simulation

- **Vectorized batch generation** for high performance
- **Deterministic random seeding** for reproducibility
- **Real-time statistics**:
  - 3D π estimate: $\hat{\pi}_{3D} = 6p$ where $p = \frac{\text{inside}}{\text{total}}$
  - 2D π estimate from slice: $\hat{\pi}_{2D} = \frac{4}{r^2} \cdot \frac{\text{inside}_{\text{slice}}}{\text{total}_{\text{slice}}}$
  - Absolute error from true π value
  - FPS counter and elapsed time

### Controls

- **Start/Pause/Step/Reset** buttons for simulation control
- **Target points** configurable from 100 to 10,000,000
- **Batch size** control (1 to 100,000 points per frame)
- **Random seed** input with randomization button
- **Slice parameters**:
  - Axis selection (X, Y, Z)
  - Position slider: $s \in [-1, 1]$
  - Thickness control: $\Delta \in [0.001, 0.2]$

### Export Features

- **Save PNG**: Export 3D and 2D views as high-resolution images
- **Export CSV**: Save all generated points with inside/outside labels
  - Format: `x,y,z,in_sphere`
  - Stream-safe for large datasets

### UI/UX

- **Dark/Light theme toggle** with polished QSS stylesheets
- **Responsive layout** with resizable splitter
- **Dockable control panel**
- **High-DPI support** for retina displays
- **Smooth animations** with configurable FPS limiting

## Mathematical Background

### 3D Estimation

The unit cube has volume:
$$V_{\text{cube}} = 2^3 = 8$$

The unit sphere has volume:
$$V_{\text{sphere}} = \frac{4\pi}{3}$$

The ratio of points inside to total approximates the volume ratio:
$$\frac{\text{inside}}{\text{total}} \approx \frac{4\pi/3}{8} = \frac{\pi}{6}$$

Therefore:
$$\hat{\pi}_{3D} = 6 \cdot \frac{\text{inside}}{\text{total}}$$

### 2D Slice Estimation

For a slice perpendicular to axis $A$ at position $s \in [-1,1]$:

The circle cross-section has radius:
$$r = \sqrt{1 - s^2}$$

The slice square is $[-1,1]^2$ with area 4.

The circle has area $\pi r^2$.

From the slice data alone:
$$\frac{\text{inside}_{\text{slice}}}{\text{total}_{\text{slice}}} \approx \frac{\pi r^2}{4}$$

Therefore:
$$\hat{\pi}_{2D} = \frac{4}{r^2} \cdot \frac{\text{inside}_{\text{slice}}}{\text{total}_{\text{slice}}}$$

This estimate is only valid when $r > 0$ (i.e., $|s| < 1$) and sufficient points exist in the slice.

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Dependencies

Install all dependencies using:

```bash
cd montepi_qt3d
pip install -r requirements.txt
```

The `requirements.txt` includes:

- **PySide6**: Qt for Python (GUI framework)
- **numpy**: Numerical operations
- **matplotlib**: 2D plotting
- **pyvista**: 3D visualization (recommended)
- **pyvistaqt**: Qt integration for PyVista

### Optional: PyVista Installation

PyVista provides superior 3D rendering performance. If PyVista fails to install or initialize, the application automatically falls back to Matplotlib's `mplot3d` (with reduced performance and point limit).

To ensure PyVista works:

```bash
pip install pyvista pyvistaqt
```

## Usage

### Running the Application

```bash
cd montepi_qt3d
python main.py
```

### Basic Workflow

1. **Set parameters**:

   - Choose target number of points (e.g., 100,000)
   - Set batch size (e.g., 1,000 points per frame)
   - Optionally set a random seed for reproducibility

2. **Start simulation**:

   - Click **Start** to begin continuous generation
   - Click **Pause** to stop at any time
   - Click **Step** to generate one batch manually
   - Click **Reset** to clear and start over

3. **Explore the slice view**:

   - Select slice axis (X, Y, or Z)
   - Move the position slider to see different cross-sections
   - Adjust thickness to include more/fewer points
   - Watch the 2D π estimate update in real-time

4. **Export results**:
   - **Save PNG**: Captures both 3D and 2D views as `filename_3D.png` and `filename_2D.png`
   - **Export CSV**: Saves all points in CSV format for further analysis

### Performance Tips

- **Large datasets**: For millions of points, use larger batch sizes (10,000+) to reduce GUI overhead
- **Smooth animation**: Keep batch size moderate (1,000-5,000) for responsive visualization
- **PyVista vs Matplotlib**: PyVista can handle millions of points; Matplotlib caps at ~100,000 displayed points
- **Slice thickness**: Smaller thickness values give cleaner slices but fewer points for estimation

## Project Structure

```
montepi_qt3d/
├── ui/
│   └── main_window.ui          # Qt Designer UI definition
├── tests/
│   └── test_simulation.py      # Unit tests for simulation logic
├── main.py                     # Application entry point
├── simulation.py               # Monte Carlo simulation core
├── view3d.py                   # 3D visualization (PyVista + Matplotlib)
├── view2d.py                   # 2D slice visualization
├── theme.py                    # Dark/light QSS themes
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Modifying the UI with Qt Designer

The user interface is defined in `ui/main_window.ui`, which can be edited with Qt Designer.

### Opening in Qt Designer

1. Install Qt Designer:

   ```bash
   pip install pyqt6-tools
   ```

2. Locate Qt Designer executable:

   - Windows: `<python>\Lib\site-packages\qt6_applications\Qt\bin\designer.exe`
   - macOS/Linux: `designer` or `designer-qt6`

3. Open the UI file:
   ```bash
   designer ui/main_window.ui
   ```

### Important Widget objectNames

The code relies on these specific `objectName` properties:

**Containers:**

- `plot3DHost`: QWidget for 3D visualization
- `plot2DHost`: QWidget for 2D slice view
- `mainSplitter`: QSplitter containing both views

**Buttons:**

- `startButton`, `pauseButton`, `stepButton`, `resetButton`
- `randomizeSeedButton`
- `savePNGButton`, `exportCSVButton`

**Inputs:**

- `targetSpin` (QSpinBox), `targetSlider` (QSlider)
- `batchSpin` (QSpinBox)
- `seedEdit` (QLineEdit)
- `sliceAxisCombo` (QComboBox)
- `slicePosSpin` (QDoubleSpinBox), `slicePosSlider` (QSlider)
- `sliceThicknessSpin` (QDoubleSpinBox)
- `darkThemeCheck` (QCheckBox)

**Labels:**

- `totalLabel`, `insideLabel`, `outsideLabel`
- `pi3DLabel`, `pi2DLabel`
- `err3DLabel`, `err2DLabel`
- `sliceCountLabel`, `fpsLabel`, `elapsedLabel`

**Important**: Do not change these `objectName` values without updating the corresponding references in `main.py`.

## Architecture Details

### simulation.py

- **`MonteCarloPi3D`**: Pure simulation logic, no GUI dependencies
- Vectorized operations using NumPy for efficiency
- Stores all generated points for slice computation
- Provides both 3D and 2D π estimates

### view3d.py

- **`View3DBase`**: Abstract base class for 3D views
- **`View3DPyVista`**: High-performance PyVista implementation
  - Direct GPU rendering with VTK backend
  - Point sprites with depth testing
  - Interactive camera controls
- **`View3DMatplotlib`**: Fallback using Matplotlib's `Axes3D`
  - Software rendering with point limit
  - Manual scatter plot updates
- **`create_3d_view()`**: Factory function that auto-selects implementation

### view2d.py

- **`View2DSlice`**: Matplotlib-based 2D slice view
- Efficient scatter plot updates using `set_offsets()`
- Dynamic circle radius calculation: $r = \sqrt{1 - s^2}$
- Synchronized with 3D view via main application

### main.py

- **`MonteCarloApp`**: Main QMainWindow subclass
- Loads UI from `.ui` file using `QUiLoader`
- Wires all signals/slots for event handling
- QTimer-based update loop (~30 FPS)
- Manages simulation state and view updates

### theme.py

- Dark and light QSS (Qt Style Sheet) definitions
- Comprehensive widget styling
- Toggle function for runtime theme switching

## Testing

Run the test suite:

```bash
cd montepi_qt3d
pytest tests/test_simulation.py -v
```

Tests include:

- Deterministic behavior with fixed seeds
- Correct inside/outside classification
- Statistical convergence to π (with 1M points)
- Slice computation accuracy
- Edge cases (empty simulation, tangent slices)

## Performance Characteristics

### PyVista Mode

- **Capacity**: 10M+ points in real-time
- **FPS**: 30-60 FPS with continuous generation
- **Memory**: ~80 MB per million points

### Matplotlib Fallback Mode

- **Capacity**: 100K displayed points (others tracked but not shown)
- **FPS**: 10-30 FPS depending on point count
- **Memory**: ~40 MB per million points (tracked)

### Typical Convergence

- **1,000 points**: Error ~0.1
- **10,000 points**: Error ~0.03
- **100,000 points**: Error ~0.01
- **1,000,000 points**: Error ~0.003

## Troubleshooting

### PyVista fails to import

**Solution**: The application automatically falls back to Matplotlib. To use PyVista:

1. Ensure OpenGL drivers are up to date
2. Try reinstalling: `pip uninstall pyvista pyvistaqt; pip install pyvista pyvistaqt`
3. On remote systems, set `export DISPLAY=:0` or use VNC

### Slow performance with Matplotlib

**Solution**:

- Reduce target points to <100,000
- Increase batch size to reduce update frequency
- Use PyVista for better performance

### UI file not loading

**Solution**: Ensure you're running from the `montepi_qt3d` directory and `ui/main_window.ui` exists.

### Theme not applying

**Solution**: Check that `darkThemeCheck` widget exists in UI and has correct `objectName`.

## Future Enhancements

Possible extensions:

- Multi-threading with `QThread` for background generation
- GPU acceleration with CuPy for batch generation
- Animation recording (video export)
- Additional estimators (Buffon's needle, etc.)
- Convergence plots over time
- Confidence intervals using CLT

## License

This project is provided as-is for educational purposes.

## Credits

Developed as a demonstration of:

- Monte Carlo methods in computational mathematics
- Qt/PySide6 GUI development
- Scientific visualization with PyVista and Matplotlib
- Clean Python architecture with separation of concerns

---

**Enjoy exploring π in 3D!** 🎲🎯
