# Atlas Simulator Program

A Mars rover simulation environment for collecting human navigation demonstrations in Godot game engine environment
to train a mapless autonomous navigation model for mars like terrain

## Requirements
- godot
- Terrain3D by Tokisan Games (godot plugin)
- numpy
- PIL
- torch
- torchvision
- tqdm
- jupyterlab

## How to collect training data from simulation
_A trained model weights are already available in `EfficientNet-B0/weights/AtlasEffB0_v0.pt`, so you don't have to collect or 
train anything again. Instructions for data collection and training are still provided for anyone who wants to reproduce the 
results, retrain the model, or experiment with different datasets_

1. Open the `godot` folder in Godot game engine and hit play
2. Use WASD to move in the 4 directions. Use K and L key to rotate left and right respectively
3. The goal is to move the rover to reach the big red beacon light
4. The data of your movements will be recorded automaticaly to `dataset/godot` folder

> [!NOTE]
> If the training doesn't collect any data, try changing the `DataCollector/collect_data` boolean parameter in godot to true

## How to train the model
1. Run `dataset/process_image_data.py`
2. Run `dataset/delete_data_bin_files.py`
3. Open jupyterlab in `EfficientNet-B0` folder
4. Run all (except the last) cells in `efficientnet_b0.ipynb`

## How to infer the model in realtime
1. Run `EfficientNet-B0/AtlasEffB0_v0_server.py` in a terminal (Keep it running for the entire duration of the simulation)
2. Open the `godot` folder in Godot game engine and hit play
3. The rover will now automatically moved by the model

> [!NOTE]
> If the rover is not moved by the model, try changing the `Rover/ModelController/use_model` boolean parameter in godot to true
