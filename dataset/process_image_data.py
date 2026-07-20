import struct
from pathlib import Path

import numpy as np
from PIL import Image

dataset_root = Path("godot")

for run_dir in sorted(dataset_root.glob("run_*")):
    data_file = run_dir / "data.bin"

    if not data_file.exists():
        print(f"Skipping {run_dir.name} (no data.bin)")
        continue

    frames_dir = run_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    print(f"Processing {run_dir.name}...")

    with open(data_file, "rb") as f:
        width = struct.unpack("<I", f.read(4))[0]
        height = struct.unpack("<I", f.read(4))[0]
        image_format = struct.unpack("<I", f.read(4))[0]

        print(f"  {width}x{height}, format={image_format}")

        frame = 0

        while True:
            frame_id_bytes = f.read(4)
            if len(frame_id_bytes) == 0:
                break
            frame_id = struct.unpack("<I", frame_id_bytes)[0]

            size_bytes = f.read(4)
            size = struct.unpack("<I", size_bytes)[0]

            data = f.read(size)
            if len(data) != size:
                print(f"  Warning: incomplete frame {frame_id}, expected {size} bytes, got {len(data)} bytes")
                break

            image = np.frombuffer(data, dtype=np.uint8)
            image = image.reshape(height, width, 3)

            Image.fromarray(image, "RGB").save(
                frames_dir / f"{frame_id}.png"
            )
            frame += 1

    print(f"  Read {frame} frames\n")

print("Done.")
