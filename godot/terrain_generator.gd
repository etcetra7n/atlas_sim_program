extends Node3D

@onready var terrain: Terrain3D = $"../Terrain3D"

signal terrain_generated
var is_generated := false

const SIZE := 1024
const HEIGHT := 130.0

var noise := FastNoiseLite.new()

func _ready():
	randomize()
	noise.seed = randi()
	noise.noise_type = FastNoiseLite.TYPE_PERLIN
	noise.frequency = 0.003
	noise.fractal_octaves = 6
	noise.fractal_gain = 0.5
	noise.fractal_lacunarity = 2.0
	var heightmap := Image.create(SIZE, SIZE, false, Image.FORMAT_RF)
	for x in range(SIZE):
		for y in range(SIZE):
			var h = noise.get_noise_2d(x, y)
			h = (h + 1.0) * 0.5
			heightmap.set_pixel(x, y, Color(h, 0, 0))
	terrain.data.import_images(
		[heightmap, null, null],
		Vector3(-SIZE / 2.0, 0.0, -SIZE / 2.0),
		0.0,
		HEIGHT
	)
	is_generated = true
	terrain_generated.emit()
