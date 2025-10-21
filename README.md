# 3D Monte Carlo π Approximation

A sophisticated desktop GUI application that demonstrates Monte Carlo approximation of π using 3D random sampling. The application generates random points in a cube $[-1,1]^3$ and checks whether they fall inside the unit sphere $x^2 + y^2 + z^2 \leq 1$.

<img width="1919" height="1028" alt="image" src="https://github.com/user-attachments/assets/387b2372-166c-4de3-94a3-29f0c071561c" />


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

# 3D Monte Carlo π Approximation

This repository contains a PySide6 desktop GUI that demonstrates Monte Carlo approximation of π by sampling points in the cube [-1,1]^3 and testing membership in the unit sphere.

## Current status

- A working Windows build is available in `dist/MontePi3D/MontePi3D.exe` (built with PyInstaller).
- Temporary build artifacts and `__pycache__` directories were cleaned from the repo. The project's virtual environment remains at `.venv/`.

## Quick start

To run the prebuilt executable (Windows):

```powershell
.\dist\MontePi3D\MontePi3D.exe
```

To run from source (requires a Python venv with dependencies):

```powershell
cd montepi_qt3d
.\.venv\Scripts\Activate.ps1
python main.py
```

## Dependencies

Install dependencies into the project venv:

```powershell
pip install -r requirements.txt
```

requirements.txt includes: PySide6, numpy, matplotlib, pyvista, pyvistaqt.

## Building a distributable

This project includes a PyInstaller spec and a helper script. Recommended workflow on Windows:

1. Activate the venv:

```powershell
.\.venv\Scripts\Activate.ps1
```

2. Run the build helper (invokes PyInstaller with `montepi.spec`):

```powershell
.\build_exe.ps1
```

If the default `dist\MontePi3D` is locked (Windows/OneDrive or running executable), build into a temporary dist path instead:

```powershell
.\.venv\Scripts\pyinstaller.exe --noconfirm --clean --distpath .\dist_new --workpath .\build_temp montepi.spec
```

## Troubleshooting notes

- If PyInstaller can't remove or overwrite `dist\MontePi3D`, it's usually because files are locked by a running process or OneDrive sync. Close the app and pause OneDrive syncing, or build to a different `--distpath` and then copy the folder into `dist`.
- If Qt platform plugin errors occur (e.g. missing `qwindows.dll`), add the PySide6 `platforms` plugin to the spec as an `--add-binary` entry or include it in `montepi.spec`.
- Inspect `build_temp\montepi\warn-montepi.txt` (or `build\montepi\warn-montepi.txt`) for missing imports and add them to `hiddenimports` in `montepi.spec` if needed.

## Repository housekeeping

- The `.venv/` folder is intentionally kept. Remove it only if you want to delete the virtual environment.
- Consider adding `dist/` and other build artifacts to `.gitignore` to avoid committing binaries:

```
# local build artifacts
dist/
build/
*.exe
.venv/
__pycache__/
```

If you want, I can add a small `clean.ps1` script to automate backup/copy/remove steps and add `dist/` to `.gitignore`.

More details and developer notes are in `README_BUILD.md` (build tips and common fixes).

---

Enjoy exploring π in 3D!
