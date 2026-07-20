import * as THREE from "three";

export function createRover() {
    const rover = new THREE.Group();

    // ---------- Body ----------
    const body = new THREE.Mesh(
        new THREE.BoxGeometry(1.2, 0.4, 1.6),
        new THREE.MeshStandardMaterial({
            color: 0x888888
        })
    );

    body.position.y = 0.5;
    rover.add(body);

    // ---------- Mast ----------
    const mast = new THREE.Mesh(
        new THREE.CylinderGeometry(0.03,0.03,0.8),
        new THREE.MeshStandardMaterial({
            color:0x444444
        })
    );
    mast.position.set(0,1.0,-0.2);
    rover.add(mast);

    // ---------- Camera ----------
    const cameraBox = new THREE.Mesh(
        new THREE.BoxGeometry(0.25,0.15,0.12),
        new THREE.MeshStandardMaterial({
            color:0x222222
        })
    );
    cameraBox.position.set(0,1.45,-0.2);
    rover.add(cameraBox);

    // ---------- Wheels ----------

    const wheelGeometry =
        new THREE.CylinderGeometry(
            0.22,
            0.22,
            0.15,
            24
        );

    const wheelMaterial =
        new THREE.MeshStandardMaterial({
            color:0x222222
        });

    const wheelPositions = [
        [-0.65,0.22,-0.55],
        [ 0.65,0.22,-0.55],

        [-0.65,0.22, 0.55],
        [ 0.65,0.22, 0.55]
    ];

    for(const p of wheelPositions){
        const wheel =
            new THREE.Mesh(
                wheelGeometry,
                wheelMaterial
            );
        wheel.rotation.z = Math.PI/2;
        wheel.position.set(...p);
        rover.add(wheel);
    }
    return rover;
}
