# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time

from simulation import MonteCarloPi3D  # uses repo's simulation.py

st.set_page_config(layout="wide", page_title="Monte Carlo π (Streamlit)")

# --- Helpers ---
def get_sim():
    if "sim" not in st.session_state:
        st.session_state.sim = MonteCarloPi3D()
        st.session_state.start_time = None
    return st.session_state.sim

def reset_sim(seed=None):
    sim = get_sim()
    sim.reset(seed)
    st.session_state.start_time = None

def subsample_points(pts, mask, max_points=100000):
    n = len(pts)
    if n <= max_points:
        return np.arange(n)
    idx = np.random.choice(n, size=max_points, replace=False)
    return idx

# --- Sidebar controls ---
st.sidebar.header("Controls")
target = st.sidebar.number_input("Target total points", value=100000, min_value=1)
batch = st.sidebar.number_input("Batch size", value=1000, min_value=1)
run_steps = st.sidebar.number_input("Run steps (N batches)", value=10, min_value=1)
seed_input = st.sidebar.text_input("Seed (leave blank for random)")
if st.sidebar.button("Randomize seed"):
    seed_input = str(np.random.randint(0, 1_000_000))
    st.sidebar.text_input("Seed (leave blank for random)", value=seed_input)

if st.sidebar.button("Reset"):
    try:
        seed = int(seed_input) if seed_input.strip() else None
    except ValueError:
        seed = None
    reset_sim(seed)

if st.sidebar.button("Step (1 batch)"):
    sim = get_sim()
    remaining = max(0, target - sim.total)
    n = min(batch, remaining)
    if n > 0:
        sim.next_batch(n)

if st.sidebar.button(f"Run {run_steps} steps"):
    sim = get_sim()
    remaining = max(0, target - sim.total)
    steps = int(run_steps)
    for _ in range(steps):
        n = min(batch, remaining)
        if n <= 0:
            break
        sim.next_batch(n)
        remaining -= n

# Slice controls
st.sidebar.header("Slice")
axis = st.sidebar.selectbox("Axis", ["X", "Y", "Z"], index=0)
slice_pos = st.sidebar.slider("Slice position s", -1.0, 1.0, 0.0, step=0.01)
thickness = st.sidebar.slider("Thickness Δ", 0.001, 0.2, 0.02, step=0.001)

# --- Main layout ---
sim = get_sim()

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("3D View (subsampled)")
    points = np.array(sim.get_all_points())
    masks = np.array(sim.get_all_masks()).astype(bool)

    if len(points) == 0:
        st.info("No points yet — press Step or Run to generate.")
    else:
        idx = subsample_points(points, masks, max_points=200000)
        df = pd.DataFrame(points[idx], columns=["x", "y", "z"])
        df["inside"] = masks[idx]
        df["color"] = df["inside"].map({True: "inside", False: "outside"})
        fig3d = px.scatter_3d(df, x="x", y="y", z="z", color="color",
                              color_discrete_map={"inside":"green","outside":"red"},
                              opacity=0.7, width=700, height=600)
        fig3d.update_traces(marker=dict(size=2))
        st.plotly_chart(fig3d, use_container_width=True)

with col2:
    st.subheader("2D Slice (projection)")
    # Compute slice projection using your simulation method if available
    axis_idx = {"X": 0, "Y": 1, "Z": 2}[axis]
    total_slice, inside_slice, pi_2d, err_2d = sim.compute_slice_stats(axis_idx, slice_pos, thickness)
    st.metric("Total points", f"{sim.total:,}")
    st.metric("Points inside", f"{sim.inside:,}")
    st.metric("π (3D)", f"{sim.pi3d:.6f}" if sim.total>0 else "—")

    # Build slice plot (project points in slab)
    if sim.total > 0 and total_slice > 0:
        all_points = np.array(sim.get_all_points())
        all_masks = np.array(sim.get_all_masks()).astype(bool)
        axis_idx = {"X":0,"Y":1,"Z":2}[axis]
        mask_slab = np.abs(all_points[:, axis_idx] - slice_pos) <= (thickness/2.0)
        proj = np.delete(all_points[mask_slab], axis_idx, axis=1)
        proj_mask = all_masks[mask_slab]

        df2 = pd.DataFrame(proj, columns=["u","v"])
        df2["inside"] = proj_mask
        fig2d = px.scatter(df2, x="u", y="v", color=df2["inside"].map({True:"inside",False:"outside"}),
                           color_discrete_map={"inside":"green","outside":"red"},
                           width=600, height=600)
        # overlay circle of radius r
        r = np.sqrt(max(0.0, 1.0 - slice_pos**2))
        theta = np.linspace(0, 2*np.pi, 200)
        circle_x = r * np.cos(theta)
        circle_y = r * np.sin(theta)
        fig2d.add_scatter(x=circle_x, y=circle_y, mode="lines", name="slice circle", line=dict(color="blue"))
        st.plotly_chart(fig2d, use_container_width=True)
        st.write(f"Slice count: {total_slice:,}  — π₂D ≈ {pi_2d:.5f}  (err {err_2d:.5f})")
    else:
        st.info("Not enough slice points to display π₂D (increase generated points or thickness).")

# Export CSV
if st.button("Export all points to CSV"):
    pts = np.array(sim.get_all_points())
    masks = np.array(sim.get_all_masks()).astype(int)
    if len(pts)>0:
        df_all = pd.DataFrame(pts, columns=["x","y","z"])
        df_all["in_sphere"] = masks
        csv = df_all.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name="montepi_points.csv", mime="text/csv")
    else:
        st.warning("No points to export.")