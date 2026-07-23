extends RigidBody3D

@onready var terrain_generator = $"../TerrainGenerator"
@onready var terrain: Terrain3D = $"../Terrain3D"

@export var engine_force := 2500.0
@export var turn_torque := 2000.0

@export var model_engine_force := 2500.0
@export var model_turn_torque := 5000.0

var model_fwd := 0.0
var model_right := 0.0
var model_steer := 0.0

func set_model_commands(fwd, right, steer):
	model_fwd = fwd
	model_right = right
	model_steer = steer

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
	
	apply_central_force(global_basis.z * model_engine_force * model_fwd)
	apply_central_force(-global_basis.x * model_engine_force * model_right)
	apply_torque(Vector3.DOWN * model_turn_torque * model_steer)
	
func _ready() -> void:
	if not terrain_generator.is_generated:
		await terrain_generator.terrain_generated
	var y = terrain.data.get_height(Vector3(0.0, 0.0, 0.0))
	global_position = Vector3(0, y + 5.0, 0)
