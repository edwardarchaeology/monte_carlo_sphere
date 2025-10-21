# Quick Start Guide

## Installation (First Time Only)

1. **Install Python** (if not already installed)

   - Download Python 3.10+ from https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Install Dependencies**
   ```bash
   cd montepi_qt3d
   pip install -r requirements.txt
   ```

## Running the Application

### Windows

Double-click `run.bat` or open PowerShell and run:

```powershell
cd montepi_qt3d
python main.py
```

### macOS/Linux

```bash
cd montepi_qt3d
python3 main.py
```

## First Use Tutorial

### Basic Operation

1. **Start with defaults**

   - Target: 100,000 points
   - Batch: 1,000 points/frame
   - Seed: 42
   - Click **Start**

2. **Watch the visualization**

   - Left panel: 3D view of points (green=inside, red=outside)
   - Right panel: 2D slice view
   - Control panel: Real-time statistics

3. **Experiment with slices**
   - Change "Slice Axis" (X, Y, or Z)
   - Move "Slice Position" slider
   - Watch how the circle size changes
   - See 2D π estimate update

### Example Experiments

#### Experiment 1: Convergence Test

```
Target: 1,000,000
Batch: 10,000
Seed: 42
```

- Watch error decrease as points accumulate
- With 1M points, error should be < 0.01

#### Experiment 2: Reproducibility

```
Run 1: Seed = 123, Target = 10,000
Run 2: Seed = 123, Target = 10,000
```

- Both runs should give identical results
- Demonstrates deterministic random generation

#### Experiment 3: Slice Analysis

```
Target: 100,000
Slice Axis: Z
Slice Position: 0.0 (center)
Thickness: 0.1
```

- Maximum circle radius (r=1.0) at center
- Move to 0.5: circle radius ≈ 0.87
- Move to 0.9: circle radius ≈ 0.44
- At ±1.0: no circle (tangent)

### Controls Reference

| Control                | Purpose                             |
| ---------------------- | ----------------------------------- |
| **Start**              | Begin continuous generation         |
| **Pause**              | Stop generation (resume with Start) |
| **Step**               | Generate one batch manually         |
| **Reset**              | Clear all and restart               |
| **Target Spin/Slider** | Set total points goal               |
| **Batch Spin**         | Points per update frame             |
| **Seed Edit**          | Set random seed                     |
| **Random Button**      | Generate random seed                |
| **Slice Axis**         | Choose X, Y, or Z plane             |
| **Slice Position**     | Move slice through volume           |
| **Slice Thickness**    | Set slab depth                      |
| **Dark Theme**         | Toggle dark/light mode              |
| **Save PNG**           | Export 3D & 2D images               |
| **Export CSV**         | Save all points as data             |

### Understanding the Statistics

**Total Points**: Number of points generated  
**Inside**: Points within unit sphere  
**Outside**: Points outside sphere  
**π (3D)**: Estimate using 3D ratio × 6  
**Error (3D)**: |estimate - π|  
**π (2D Slice)**: Estimate from slice data alone  
**Error (2D)**: |slice_estimate - π|  
**Slice Points**: Points in current slice  
**FPS**: Update rate (frames per second)  
**Elapsed**: Time since start

### Tips for Best Results

✅ **DO:**

- Use batch size 1,000-5,000 for smooth animation
- Use larger batches (10,000+) for fast generation
- Export CSV for statistical analysis
- Try different seeds to see variation
- Explore slices at different positions

❌ **AVOID:**

- Very small batches (<100) - slow and inefficient
- Millions of points without PyVista (use fallback limit)
- Slice position exactly ±1.0 (tangent, no estimate)
- Extremely thin slices (<0.01) with few points

### Keyboard Shortcuts

- **Space**: Start/Pause (when focused on Start button)
- **Alt+T**: Toggle theme (if accelerator set)
- **Mouse wheel**: Zoom 3D view
- **Left drag**: Rotate 3D view
- **Right drag**: Pan 3D view

### Troubleshooting

**Problem**: Application won't start  
**Solution**: Run `pip install -r requirements.txt`

**Problem**: 3D view is slow  
**Solution**: PyVista may not be available; this is expected fallback behavior

**Problem**: Slice shows no points  
**Solution**: Increase slice thickness or ensure points exist in that region

**Problem**: 2D π estimate shows "—"  
**Solution**: Move slice away from ±1.0 or increase point count

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Run tests: `pytest tests/test_simulation.py -v`
- Modify UI in Qt Designer: `designer ui/main_window.ui`
- Export data for analysis in Excel, Python, or R

---

**Have fun exploring Monte Carlo methods!** 🎲
