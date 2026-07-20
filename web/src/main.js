import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { STLLoader } from "three/examples/jsm/loaders/STLLoader.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { createRover } from "./Rover.js";

// --------------------------------------------------
// Scene
// --------------------------------------------------

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x020202);

// --------------------------------------------------
// Renderer
// --------------------------------------------------

const renderer = new THREE.WebGLRenderer({
    antialias: true
});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
document.body.style.margin = "0";
document.body.appendChild(renderer.domElement);

// --------------------------------------------------
// Lights
// --------------------------------------------------

scene.add(new THREE.AmbientLight(0xffffff, 0.5));
const sun = new THREE.DirectionalLight(0xffffff, 2.5);
sun.position.set(100, 150, 80);
scene.add(sun);

// --------------------------------------------------
// Spectator Camera
// --------------------------------------------------

const spectatorCamera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);

spectatorCamera.position.set(20, 20, 20);
const controls = new OrbitControls(
    spectatorCamera,
    renderer.domElement
);
controls.target.set(0, 0, 0);

// --------------------------------------------------
// Terrain
// --------------------------------------------------

let terrain = null;

const stlLoader = new STLLoader();

stlLoader.load("/terrains/terrain.stl", geometry => {
    geometry.computeVertexNormals();
    const material = new THREE.MeshStandardMaterial({
        color: 0xaa7744
    });
    terrain = new THREE.Mesh(geometry, material);
    terrain.rotation.x = -Math.PI / 2;
    scene.add(terrain);

});

// --------------------------------------------------
// Rover
// --------------------------------------------------
const roverRoot = new THREE.Group();
const roverBody = createRover();
const roverCamera = new THREE.PerspectiveCamera(
    80,
    window.innerWidth/window.innerHeight,
    0.05,
    200
);
roverCamera.position.set(
    0,
    1.45,
    -0.2
);
roverCamera.rotation.x = THREE.MathUtils.degToRad(-15);
roverBody.add(roverCamera);
roverRoot.add(roverBody);
scene.add(roverRoot);

// --------------------------------------------------
// Keyboard
// --------------------------------------------------

const keys = {};

window.addEventListener("keydown", e => {
    keys[e.key.toLowerCase()] = true;
});

window.addEventListener("keyup", e => {
    keys[e.key.toLowerCase()] = false;
});

// --------------------------------------------------
// Rover Motion
// --------------------------------------------------

const moveSpeed = 1;
const rotateSpeed = 0.5;
const wheelRadius = 0.05;
const bodyHeight = 0.55;
const wheelOffsets = [
    new THREE.Vector3(-0.7, 0,  0.8), // FL
    new THREE.Vector3( 0.7, 0,  0.8), // FR
    new THREE.Vector3(-0.7, 0, -0.8), // RL
    new THREE.Vector3( 0.7, 0, -0.8), // RR
];

const clock = new THREE.Clock();
const raycaster = new THREE.Raycaster();
const down = new THREE.Vector3(0, -1, 0);
const up = new THREE.Vector3(0, 1, 0);
const quaternion = new THREE.Quaternion();
const rayOrigin = new THREE.Vector3();
const h_average = new THREE.Vector3();
const hits = [];

let roverYaw = 0;

function updateRover(dt) {
    if (!terrain) return;

    if (keys["k"])
        roverYaw += rotateSpeed * dt;

    if (keys["l"])
        roverYaw -= rotateSpeed * dt;

    const forward = new THREE.Vector3(
        Math.sin(roverYaw),
        0,
        -Math.cos(roverYaw)
    );
    const right = new THREE.Vector3(
        Math.cos(roverYaw),
        0,
        Math.sin(roverYaw)
    );

    if (keys["w"])
        roverRoot.position.addScaledVector(forward, moveSpeed * dt);
    if (keys["s"])
        roverRoot.position.addScaledVector(forward, -moveSpeed * dt);
    if (keys["d"])
        roverRoot.position.addScaledVector(right, moveSpeed * dt);
    if (keys["a"])
        roverRoot.position.addScaledVector(right, -moveSpeed * dt);

    // -----------------------------
    // Raycast wheels
    // -----------------------------

    hits.length = 0;
    for (const offset of wheelOffsets) {
        const origin = offset.clone();
        roverRoot.localToWorld(origin);
        origin.y += 10;
        raycaster.set(origin, down);
        const result = raycaster.intersectObject(terrain, true);
        if (result.length)
            hits.push(result[0]);
    }
    if (hits.length !== 4)
        return;

    // -----------------------------
    // Average wheel position
    // -----------------------------

    h_average.set(0, 0, 0);
    for (const h of hits)
        h_average.add(h.point);
    h_average.divideScalar(4);
    roverRoot.position.y = THREE.MathUtils.lerp(
        roverRoot.position.y,
        h_average.y + bodyHeight,
        8 * dt
    );

    // -----------------------------
    // Terrain orientation
    // -----------------------------
    const front = hits[0].point.clone()
        .add(hits[1].point)
        .multiplyScalar(0.5);
    const rear = hits[2].point.clone()
        .add(hits[3].point)
        .multiplyScalar(0.5);
    const left = hits[0].point.clone()
        .add(hits[2].point)
        .multiplyScalar(0.5);
    const rightMid = hits[1].point.clone()
        .add(hits[3].point)
        .multiplyScalar(0.5);
    const terrainForward = front.sub(rear).normalize();
    const terrainRight = rightMid.sub(left).normalize();
    const terrainNormal = new THREE.Vector3()
        .crossVectors(terrainRight, terrainForward)
        .normalize();

    // Keep driver's heading while following terrain
    const desiredForward = forward.clone()
        .projectOnPlane(terrainNormal)
        .normalize();
    const desiredRight = new THREE.Vector3()
        .crossVectors(desiredForward, terrainNormal)
        .normalize();
    desiredForward
        .crossVectors(terrainNormal, desiredRight)
        .normalize();

    const matrix = new THREE.Matrix4();
    matrix.makeBasis(
        desiredRight,
        terrainNormal,
        desiredForward.clone().negate()
    );
    const targetQuat = new THREE.Quaternion().setFromRotationMatrix(matrix);
    roverRoot.quaternion.slerp(
        targetQuat,
        6 * dt
    );
}

// --------------------------------------------------
// Render Loop
// --------------------------------------------------

function animate() {
    requestAnimationFrame(animate);
    const dt = clock.getDelta();
    updateRover(dt);
    controls.update();
    if (roverCamera)
        renderer.render(scene, roverCamera);
    else
        renderer.render(scene, spectatorCamera);
}
animate();

// --------------------------------------------------
// Resize
// --------------------------------------------------

window.addEventListener("resize", () => {
    renderer.setSize(
        window.innerWidth,
        window.innerHeight
    );
    spectatorCamera.aspect =
        window.innerWidth / window.innerHeight;
    spectatorCamera.updateProjectionMatrix();
    if (roverCamera) {
        roverCamera.aspect =
            window.innerWidth / window.innerHeight;
        roverCamera.updateProjectionMatrix();
    }
});