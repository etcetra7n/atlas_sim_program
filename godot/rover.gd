extends RigidBody3D

@onready var terrain_generator = $"../TerrainGenerator"
@onready var terrain: Terrain3D = $"../Terrain3D"

@export var engine_force := 2500.0
@export var turn_torque := 2000.0

func _physics_process(_dt):
	if Input.is_action_pressed("forward"):
		apply_central_force(global_basis.z * engine_force)
	if Input.is_action_pressed("reverse"):
		apply_central_force(-global_basis.z * engine_force)
	if Input.is_action_pressed("left"):
		apply_central_force(global_basis.x * engine_force)
	if Input.is_action_pressed("right"):
		apply_central_force(-global_basis.x * engine_force)
	if Input.is_action_pressed("rotate_left"):
		apply_torque(Vector3.UP * turn_torque)
	if Input.is_action_pressed("rotate_right"):
		apply_torque(Vector3.DOWN * turn_torque)

func _ready() -> void:
	if not terrain_generator.is_generated:
		await terrain_generator.terrain_generated
	var y = terrain.data.get_height(Vector3(0.0, 0.0, 0.0))
	global_position = Vector3(0, y + 5.0, 0)
