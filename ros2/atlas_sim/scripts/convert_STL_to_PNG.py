 #!/usr/bin/env python3

import numpy as np
import trimesh
from PIL import Image

# -----------------------------
# Configuration
# -----------------------------
STL_FILE = "../meshes/w2.stl"
OUTPUT = "../worlds/heightmap_w2.png"

RESOLUTION = 1024       # Output image size
MARGIN = 1e-3           # Rays start slightly above mesh

# -----------------------------
# Load mesh
# -----------------------------
print("Loading STL...")
mesh = trimesh.load(STL_FILE, force="mesh")

if mesh.is_empty:
    raise RuntimeError("Failed to load mesh")

print(mesh)

# -----------------------------
# Bounding box
# -----------------------------
xmin, ymin, zmin = mesh.bounds[0]
xmax, ymax, zmax = mesh.bounds[1]

print("Bounds:")
print(mesh.bounds)

# -----------------------------
# Generate XY grid
# -----------------------------
x = np.linspace(xmin, xmax, RESOLUTION)
y = np.linspace(ymin, ymax, RESOLUTION)

xx, yy = np.meshgrid(x, y)

origins = np.column_stack([
    xx.ravel(),
    yy.ravel(),
    np.full(xx.size, zmax + MARGIN)
])

directions = np.tile([0.0, 0.0, -1.0], (origins.shape[0], 1))

print(f"Casting {origins.shape[0]:,} rays...")

# -----------------------------
# Ray intersection
# -----------------------------
locations, ray_ids, triangle_ids = mesh.ray.intersects_location(
    origins,
    directions,
    multiple_hits=False
)

# -----------------------------
# Build height array
# -----------------------------
height = np.full(origins.shape[0], zmin)

height[ray_ids] = locations[:, 2]

height = height.reshape((RESOLUTION, RESOLUTION))

# Flip vertically for image coordinates
height = np.flipud(height)

# -----------------------------
# Normalize to 16-bit
# -----------------------------
height -= height.min()

max_height = height.max()

if max_height > 0:
    height /= max_height

height16 = np.round(height * 65535).astype(np.uint16)

print("Saving PNG...")

Image.fromarray(height16, mode="I;16").save(OUTPUT)

print("Done.")
print("Height range:", zmin, "to", zmax)
print("Saved:", OUTPUT)