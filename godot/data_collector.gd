extends Node

@onready var destination = $"../Destination"
@onready var rover = $"../Rover"
@onready var viewport: Viewport = get_viewport() #$"../Rover/SubViewport"

@export_range(1, 60)
var capture_fps := 15

const DATASET_DIR = "res://../dataset/godot/"

var frame := 0
var run_dir := ""
var dest_pos
var data_file
var label_file

var mv_fwd: int = 0
var mv_right: int = 0
var steer: int = 0

func _ready():
	var dataset_root = ProjectSettings.globalize_path(DATASET_DIR)
	DirAccess.make_dir_recursive_absolute(dataset_root)
	
	var next_run = _get_next_run_number(dataset_root)
	run_dir = dataset_root.path_join("run_%04d" % next_run)
	DirAccess.make_dir_recursive_absolute(run_dir)
	
	print("Recording to: ", run_dir)
	
	data_file = FileAccess.open(
		run_dir.path_join("data.bin"), 
		FileAccess.WRITE
	)
	if data_file == null:
		push_error("Failed to open data.bin")
		return
	data_file.store_32(640)
	data_file.store_32(360)
	data_file.store_32(Image.FORMAT_RGBA8)
	
	label_file = FileAccess.open(
		run_dir.path_join("labels.jsonl"), 
		FileAccess.WRITE
	)
	if label_file == null:
		push_error("Failed to open labels.jsonl")
		return
	$Timer.timeout.connect(_on_timer_timeout)
	$Timer.wait_time = 1.0 / capture_fps
	
	if destination.destination_pos == null:
		await destination.destination_generated
	dest_pos = destination.destination_pos
	await RenderingServer.frame_post_draw
	await get_tree().process_frame
	$Timer.start()

func _on_timer_timeout():
	var img := viewport.get_texture().get_image()
	img.resize(640, 360, Image.INTERPOLATE_BILINEAR)
	var data := img.get_data()
	data_file.store_32(frame)
	data_file.store_32(data.size())
	data_file.store_buffer(data)
	
	mv_fwd = 0
	mv_right = 0
	steer = 0
	if Input.is_action_pressed("forward"):
		mv_fwd = 1
	if Input.is_action_pressed("reverse"):
		mv_fwd = -1
	if Input.is_action_pressed("right"):
		mv_right = 1
	if Input.is_action_pressed("left"):
		mv_right = -1
	if Input.is_action_pressed("rotate_right"):
		steer = 1
	if Input.is_action_pressed("rotate_left"):
		steer = -1

	var sample = {
		"frame_id": frame,
		"dest_x": dest_pos.x,
		"dest_y": dest_pos.z,
		
		"pos_x": rover.global_position.x,
		"pos_y": rover.global_position.z,
		"fwd_x": (rover.global_transform.basis.z).x,
		"fwd_y": (rover.global_transform.basis.z).y,
		"fwd_z": (rover.global_transform.basis.z).z,
		
		"mv_fwd": mv_fwd,
		"mv_right": mv_right,
		"steer": steer,
	}
	label_file.store_line(JSON.stringify(sample))
	frame += 1

func _exit_tree():
	if data_file:
		data_file.close()
	if label_file:
		label_file.close()

func _get_next_run_number(dataset_root: String) -> int:
	var highest := 0
	var dir = DirAccess.open(dataset_root)
	if dir == null:
		return 1
	dir.list_dir_begin()
	while true:
		var dir_name = dir.get_next()
		if dir_name == "":
			break
		if dir.current_is_dir() and dir_name.begins_with("run_"):
			var num = dir_name.substr(4).to_int()
			highest = maxi(highest, num)
	dir.list_dir_end()
	return highest + 1
