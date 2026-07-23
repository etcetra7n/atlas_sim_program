extends Node3D

const HOST := "127.0.0.1"
const PORT := 5000

@onready var rover: RigidBody3D = get_parent() as RigidBody3D
@onready var destination = $"../../Destination"
@onready var viewport: Viewport = get_viewport()

@export var use_model = true
@export_range(1, 60) var inference_fps := 15

var tcp := StreamPeerTCP.new()
var inference_running := false
var dest

func _ready():
	if !use_model:
		return
	var err = tcp.connect_to_host(HOST, PORT)
	if err != OK:
		push_error("Failed to connect.")
		return
	print("Connecting...")
	
	$ModelTimer.timeout.connect(_on_inference_timer_timeout)
	$ModelTimer.wait_time = 1.0 / inference_fps
	
	if destination.destination_pos == null:
		await destination.destination_generated
	dest = destination.destination_pos

	await RenderingServer.frame_post_draw
	print("ff")
	
	while tcp.get_status() == StreamPeerTCP.STATUS_CONNECTING:
		tcp.poll()
		print(tcp.get_status())
		await get_tree().process_frame
	print("Connected! Status =", tcp.get_status())
	
	if tcp.get_status() != StreamPeerTCP.STATUS_CONNECTED:
		push_error("Connection failed.")
		return
	print("here 2")
	$ModelTimer.start()

func _on_inference_timer_timeout():
	if inference_running:
		return
	inference_running = true
	
	if tcp.get_status() != StreamPeerTCP.STATUS_CONNECTED:
		inference_running = false
		return
		
	await RenderingServer.frame_post_draw
	var img := viewport.get_texture().get_image()
	img.resize(640, 360, Image.INTERPOLATE_BILINEAR)
	var png_bytes := img.save_png_to_buffer()

	var pos := rover.global_position
	var fwd := rover.global_transform.basis.z

	var packet := PackedByteArray()
	packet.resize(28)

	packet.encode_float(0, dest.x - pos.x)
	packet.encode_float(4, dest.z - pos.z)

	packet.encode_float(8, pos.x)
	packet.encode_float(12, pos.z)

	packet.encode_float(16, fwd.x)
	packet.encode_float(20, fwd.y)
	packet.encode_float(24, fwd.z)

	packet.append_array(png_bytes)

	tcp.put_u32(packet.size())
	tcp.put_data(packet)

	while tcp.get_available_bytes() < 12:
		await get_tree().process_frame
	var result = tcp.get_data(12)
	if result[0] != OK:
		inference_running = false
		return

	var bytes: PackedByteArray = result[1]
	rover.set_model_commands(
		bytes.decode_float(0),
		bytes.decode_float(4),
		bytes.decode_float(8)
	)
	inference_running = false
