import socket
import struct
from io import BytesIO

import torch
import torch.nn as nn
from torchvision.models import efficientnet_b0
from torchvision import transforms
from PIL import Image

class AtlasEffB0(nn.Module):
    def __init__(self):
        super().__init__()

        self.backbone = efficientnet_b0(weights="DEFAULT")

        self.backbone.classifier = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(1280, 128)
        )

        self.head = nn.Sequential(
            nn.Linear(135, 64),
            nn.ReLU(),
            nn.Linear(64, 3)
        )

    def forward(self, images, states):
        features = self.backbone(images)
        x = torch.cat([features, states], dim=1)
        return self.head(x)

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

model = AtlasEffB0().to(device)

checkpoint = torch.load(
    "weights/AtlasEffB0_v0.pt",
    map_location=device,
    weights_only=True
)

model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

transform = transforms.Compose([
    transforms.Resize((360, 640)),
    transforms.ToTensor(),
])

def recv_exact(sock, size):
    data = b""

    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet:
            return None
        data += packet
    return data

HOST = "127.0.0.1"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind((HOST, PORT))
server.listen(1)

print(f"Listening on {HOST}:{PORT}")

conn, addr = server.accept()
print(f"Connected from {addr}")

STATE_SIZE = 7 * 4  # 7 float32 values

try:
    while True:
        header = recv_exact(conn, 4)

        if header is None:
            print("Client disconnected.")
            break
        
        packet_size = struct.unpack("<I", header)[0]
        packet = recv_exact(conn, packet_size)

        if packet is None:
            break

        state_values = struct.unpack("<7f", packet[:STATE_SIZE])
        state = torch.tensor(
            [state_values],
            dtype=torch.float32,
            device=device
        )

        image_bytes = packet[STATE_SIZE:]
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        image = transform(image)
        image = image.unsqueeze(0).to(device)

        with torch.no_grad():
            prediction = model(image, state)

        mv_fwd = prediction[0, 0].item()
        mv_right = prediction[0, 1].item()
        steer = prediction[0, 2].item()

        print(
            f"fwd={mv_fwd:.3f} "
            f"right={mv_right:.3f} "
            f"steer={steer:.3f}"
        )

        conn.sendall(
            struct.pack(
                "<3f",
                mv_fwd,
                mv_right,
                steer
            )
        )

except KeyboardInterrupt:
    print("\nStopping server...")

finally:
    conn.close()
    server.close()
