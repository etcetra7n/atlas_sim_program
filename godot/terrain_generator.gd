extends Node3D
@onready var terrain: Terrain3D = $"../Terrain3D"

## Procedural Mars-like terrain generator for Terrain3D.
##
## Instead of a single noise layer, the terrain is built from several
## layers blended together via a large-scale "biome" mask:
##   - Continent noise    -> decides where plains vs. mountains appear
##   - Plains noise       -> gentle, low-relief rolling ground
##   - Mountain noise     -> ridged noise for sharp peaks/ridgelines
##   - Plateau terracing  -> flattens parts of the mountains into mesas
##   - Detail noise       -> small-scale surface roughness
##   - Domain warp        -> bends sample coordinates so shapes look
##                           organic instead of grid-aligned
##   - Impact craters     -> scattered bowl+rim depressions, Mars-style
signal terrain_generated
var is_generated := false

const SIZE := 1024
const HEIGHT := 130.0

@export_category("Seed")
@export var fixed_seed: int = 0 ## 0 = pick a new random seed every run

@export_category("Biomes")
@export_range(0.0005, 0.02) var biome_frequency := 0.0018 ## lower = larger continents
@export_range(0.0, 1.0) var biome_sharpness := 0.65 ## higher = crisper borders between plains/mountains
@export_range(0.0, 1.0) var mountain_threshold := 0.68 ## higher = LESS mountain area / MORE plains area (0.5 = roughly even split)

@export_category("Plains")
@export_range(0.0, 1.0) var plains_base_height := 0.18
@export_range(0.0, 0.5) var plains_amplitude := 0.08

@export_category("Mountains")
@export_range(0.0, 1.0) var mountain_base_height := 0.28
@export_range(0.2, 1.5) var mountain_amplitude := 0.85
@export_range(0.5, 4.0) var mountain_sharpness := 1.7 ## higher = narrower, sharper peaks

@export_category("Plateaus / Mesas")
@export_range(0.0, 1.0) var plateau_amount := 0.55 ## how much of the mountain area gets terraced
@export_range(2.0, 16.0) var plateau_steps := 7.0 ## number of terrace levels
@export_range(0.0, 1.0) var plateau_softness := 0.35 ## 0 = hard steps, 1 = fully smooth

@export_category("Surface Detail")
@export_range(0.0, 0.2) var detail_amplitude := 0.035

@export_category("Domain Warp")
@export_range(0.0, 200.0) var warp_strength := 40.0 ## breaks up grid-like noise patterns

@export_category("Impact Craters")
@export_range(0, 200, 1) var crater_count := 55
@export_range(4.0, 40.0) var crater_min_radius := 8.0
@export_range(20.0, 160.0) var crater_max_radius := 75.0
@export_range(0.0, 1.0) var crater_depth := 0.35

var _rng := RandomNumberGenerator.new()

var _continent_noise := FastNoiseLite.new()
var _plains_noise := FastNoiseLite.new()
var _mountain_noise := FastNoiseLite.new()
var _plateau_mask_noise := FastNoiseLite.new()
var _detail_noise := FastNoiseLite.new()
var _warp_noise_x := FastNoiseLite.new()
var _warp_noise_y := FastNoiseLite.new()


func _ready() -> void:
	if fixed_seed != 0:
		_rng.seed = fixed_seed
	else:
		_rng.randomize()

	_setup_noise()

	var start_time := Time.get_ticks_msec()

	var heightmap := Image.create(SIZE, SIZE, false, Image.FORMAT_RF)
	_generate_base_terrain(heightmap)
	_stamp_craters(heightmap)

	terrain.data.import_images(
		[heightmap, null, null],
		Vector3(-SIZE / 2.0, 0.0, -SIZE / 2.0),
		0.0,
		HEIGHT
	)

	var elapsed := (Time.get_ticks_msec() - start_time) / 1000.0
	print("Terrain generated in %.2f s" % elapsed)

	is_generated = true
	terrain_generated.emit()


func _setup_noise() -> void:
	var base_seed := _rng.randi()

	_continent_noise.seed = base_seed
	_continent_noise.noise_type = FastNoiseLite.TYPE_PERLIN
	_continent_noise.frequency = biome_frequency
	_continent_noise.fractal_octaves = 3
	_continent_noise.fractal_gain = 0.5
	_continent_noise.fractal_lacunarity = 2.0

	_plains_noise.seed = base_seed + 1
	_plains_noise.noise_type = FastNoiseLite.TYPE_PERLIN
	_plains_noise.frequency = 0.006
	_plains_noise.fractal_octaves = 4
	_plains_noise.fractal_gain = 0.35
	_plains_noise.fractal_lacunarity = 2.0

	_mountain_noise.seed = base_seed + 2
	_mountain_noise.noise_type = FastNoiseLite.TYPE_PERLIN
	_mountain_noise.frequency = 0.0045
	_mountain_noise.fractal_octaves = 6
	_mountain_noise.fractal_gain = 0.5
	_mountain_noise.fractal_lacunarity = 2.1

	_plateau_mask_noise.seed = base_seed + 3
	_plateau_mask_noise.noise_type = FastNoiseLite.TYPE_PERLIN
	_plateau_mask_noise.frequency = 0.004
	_plateau_mask_noise.fractal_octaves = 2

	_detail_noise.seed = base_seed + 4
	_detail_noise.noise_type = FastNoiseLite.TYPE_PERLIN
	_detail_noise.frequency = 0.05
	_detail_noise.fractal_octaves = 3
	_detail_noise.fractal_gain = 0.5

	_warp_noise_x.seed = base_seed + 5
	_warp_noise_x.noise_type = FastNoiseLite.TYPE_PERLIN
	_warp_noise_x.frequency = 0.004

	_warp_noise_y.seed = base_seed + 6
	_warp_noise_y.noise_type = FastNoiseLite.TYPE_PERLIN
	_warp_noise_y.frequency = 0.004


## Returns a 0..1 factor: 0 = pure plains, 1 = pure mountains.
func _biome_factor(x: float, y: float) -> float:
	var continent := (_continent_noise.get_noise_2d(x, y) + 1.0) * 0.5
	var half_width := lerpf(0.5, 0.02, biome_sharpness)
	# mountain_threshold shifts how much of the continent noise range counts
	# as "mountain": raising it shrinks mountain area and grows plains area.
	return smoothstep(mountain_threshold - half_width, mountain_threshold + half_width, continent)


func _generate_base_terrain(heightmap: Image) -> void:
	for x in range(SIZE):
		for y in range(SIZE):
			# Domain warp: perturb sample coordinates so features don't look grid-aligned
			var wx := x + _warp_noise_x.get_noise_2d(x, y) * warp_strength
			var wy := y + _warp_noise_y.get_noise_2d(x, y) * warp_strength

			# Large-scale biome mask decides plains vs. mountains
			var biome := _biome_factor(wx, wy)

			# Plains: gentle rolling terrain
			var plains_n := (_plains_noise.get_noise_2d(wx, wy) + 1.0) * 0.5
			var plains_h := plains_base_height + plains_n * plains_amplitude

			# Mountains: ridged noise for sharp peaks and ridgelines
			var raw_mountain := _mountain_noise.get_noise_2d(wx, wy)
			var ridged := pow(1.0 - abs(raw_mountain), mountain_sharpness)

			# Plateaus: terrace patches of the mountains into flat-topped mesas
			var plateau_mask := (_plateau_mask_noise.get_noise_2d(wx, wy) + 1.0) * 0.5
			var terraced := floorf(ridged * plateau_steps) / plateau_steps
			terraced = lerpf(terraced, ridged, plateau_softness)
			var plateau_threshold := 1.0 - plateau_amount
			var plateau_blend := smoothstep(plateau_threshold - 0.15, plateau_threshold + 0.15, plateau_mask)
			var mountain_shape := lerpf(ridged, terraced, plateau_blend)
			var mountain_h := mountain_base_height + mountain_shape * mountain_amplitude

			# Blend plains and mountains based on the biome mask
			var h := lerpf(plains_h, mountain_h, biome)

			# Fine surface roughness, stronger in mountainous terrain
			var detail := _detail_noise.get_noise_2d(x, y)
			h += detail * detail_amplitude * (0.4 + 0.6 * biome)

			h = clamp(h, 0.0, 1.0)
			heightmap.set_pixel(x, y, Color(h, 0.0, 0.0))


func _stamp_craters(heightmap: Image) -> void:
	for i in range(crater_count):
		var cx := _rng.randi_range(0, SIZE - 1)
		var cy := _rng.randi_range(0, SIZE - 1)
		var radius := _rng.randf_range(crater_min_radius, crater_max_radius)

		# Bigger impacts carve deeper craters; craters are also shallower
		# on steep mountain terrain, as if partly erased by younger uplift.
		var mountain_factor := _biome_factor(cx, cy)
		var depth_scale := crater_depth * _rng.randf_range(0.6, 1.0)
		depth_scale *= radius / crater_max_radius
		depth_scale *= lerpf(1.0, 0.5, mountain_factor)

		var min_x := maxi(0, int(cx - radius) - 1)
		var max_x := mini(SIZE - 1, int(cx + radius) + 1)
		var min_y := maxi(0, int(cy - radius) - 1)
		var max_y := mini(SIZE - 1, int(cy + radius) + 1)

		for x in range(min_x, max_x + 1):
			for y in range(min_y, max_y + 1):
				var dist := Vector2(x - cx, y - cy).length()
				if dist >= radius:
					continue
				var t := dist / radius
				var bowl := t * t - 1.0                            # -1 at center -> 0 at rim
				var rim := exp(-pow((t - 0.82) * 7.0, 2.0)) * 0.45  # raised rim near the edge
				var falloff := 1.0 - smoothstep(0.85, 1.0, t)       # fade out smoothly at the crater edge
				var delta := (bowl + rim) * depth_scale * falloff

				var c := heightmap.get_pixel(x, y)
				var new_h := clampf(c.r + delta, 0.0, 1.0)
				heightmap.set_pixel(x, y, Color(new_h, 0.0, 0.0))
