from pathlib import Path

dataset_root = Path("godot")

for run_dir in sorted(dataset_root.glob("run_*")):
    data_file = run_dir / "data.bin"

    if not data_file.exists():
        print(f"Skipping {run_dir.name} (no data.bin)")
        continue

    frames_dir = run_dir / "frames"
    if not frames_dir.exists():
        print(f"Skipping {run_dir.name} (no frames directory)")
        continue
    data_file.unlink()
    print(f"Deleted data.bin from {run_dir.name}.")

print("Done.")
