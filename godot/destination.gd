extends Node3D

@onready var terrain_generator = $"../TerrainGenerator"
@onready var terrain: Terrain3D = $"../Terrain3D"
@onready var beam: MeshInstance3D = $Beam

signal destination_generated(position: Vector3)
var destination_pos = null
 
const MAX_RADIUS := 100 # radius in m
const BEAM_HEIGHT := 50

func _ready():
	var angle = randf() * TAU
	var radius = sqrt(randf()) * MAX_RADIUS
	
	var x = cos(angle) * radius
	var z = sin(angle) * radius
	
	if not terrain_generator.is_generated:
		await terrain_generator.terrain_generated
	var y = terrain.data.get_height(Vector3(x, 0.0, z))
	
	destination_pos = Vector3(x, y - 8.0, z)
	global_position = destination_pos
	destination_generated.emit(destination_pos)
