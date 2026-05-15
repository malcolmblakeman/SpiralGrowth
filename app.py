import io
import random
import base64
from collections import defaultdict

import numpy as np
import streamlit as st
from PIL import Image


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="Spiral Growth Simulator",
    layout="wide",
)

st.title("Spiral Growth Simulator")


GIF_SIZE = 500


# ============================================================
# CORE FUNCTIONS
# ============================================================

def encode(x, y):
    return (x << 32) ^ (y & 0xffffffff)


def spiral_move(x, y):
    w = max(abs(x), abs(y))

    if y == -w:
        return x + 1, y
    if x == -w:
        return x, y - 1
    if y == w:
        return x - 1, y

    return x, y + 1


def hex_to_rgb(h):
    h = h.lstrip("#")
    return np.array([
        int(h[0:2], 16),
        int(h[2:4], 16),
        int(h[4:6], 16),
    ], dtype=np.uint8)


# ============================================================
# PIECES
# ============================================================

PIECES = {
    "Knight": [(-1,2),(1,2),(-2,1),(2,1),(-2,-1),(2,-1),(1,-2),(-1,-2)],
    "King": [(-1,1),(0,1),(1,1),(-1,0),(1,0),(-1,-1),(0,-1),(1,-1)],
    "Wazir": [(0,1),(-1,0),(1,0),(0,-1)],
    "Ferz": [(-1,1),(1,1),(-1,-1),(1,-1)],
    "Camel": [ (-1, 3), (1, 3), (-3, 1), (3, 1), (-3, -1), (3, -1), (1, -3), (-1, -3), ], 
    "Zebra": [ (-2, 3), (2, 3), (-3, 2), (3, 2), (-3, -2), (3, -2), (2, -3), (-2, -3), ], 
    "Giraffe": [ (-1, 4), (1, 4), (-4, 1), (4, 1), (-4, -1), (4, -1), (1, -4), (-1, -4), ], 
    "Antelope": [(-4,3),(4,3),(-3,4),(3,4),(-4,-3),(4,-3),(-3,-4),(3,-4)],
    "Eland": [(-5,3),(5,3),(-3,5),(3,5),(-5,-3),(5,-3),(-3,-5),(3,-5)],
    "Satrap": [(-2,0),(2,0)],
    "Aspbad": [(-2,2),(2,2),(-2,-2),(2,-2)],
    "Spehbed": [(-3,0),(3,0)],
    "Marzban": [(-3,3),(3,3),(-3,-3),(3,-3)],
    "PawnNorth": [(0, 1)], "PawnSouth": [(0, -1)], "PawnEast": [(1, 0)], "PawnWest": [(-1, 0)],
}


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Simulation")

num_players = st.sidebar.slider("Players", 1, 8, 3)
turns = st.sidebar.slider("Turns", 100, 100000, 10000, step=100)

bg = hex_to_rgb(st.sidebar.color_picker("Background", "#FFFFFF"))

turn_mode = st.sidebar.selectbox("Turn Order", ["Cyclic", "Random"])

fps = st.sidebar.slider("Playback FPS", 10, 60, 30)

make_animation = st.sidebar.checkbox("Build Frames", True)


# ============================================================
# PLAYERS
# ============================================================

default_colors = [
    "#FF0000",  # red
    "#0000FF",  # blue
    "#00AA00",  # green
    "#FF00FF",  # magenta

    "#00CCCC",  # cyan
    "#FF8800",  # orange
    "#888888",  # gray
    "#8800FF",  # purple
]
# ============================================================
# RANDOMIZE PLAYERS
# ============================================================

if "random_seed" not in st.session_state:
    st.session_state.random_seed = 0

if st.sidebar.button("🎲 Randomize Players"):

    st.session_state.random_seed += 1

    rng = random.Random(
        st.session_state.random_seed
    )

    shuffled_colors = default_colors.copy()
    rng.shuffle(shuffled_colors)

    random_pieces = [
        rng.choice(list(PIECES.keys()))
        for _ in range(num_players)
    ]

    st.session_state.randomized_colors = shuffled_colors
    st.session_state.randomized_pieces = random_pieces

#configs = []

# for i in range(num_players):
#     st.sidebar.subheader(f"Player {i+1}")

#     piece = st.sidebar.selectbox(
#         f"Piece {i+1}",
#         list(PIECES.keys()),
#         key=f"p{i}",
#     )

#     color = st.sidebar.color_picker(
#         f"Color {i+1}",
#         default_colors[i % len(default_colors)],
#         key=f"c{i}",
#     )

#     configs.append({
#         "piece": piece,
#         "color": hex_to_rgb(color),
#     })

configs = []

for i in range(num_players):

    st.sidebar.subheader(f"Player {i+1}")

    # ----------------------------------------
    # defaults
    # ----------------------------------------

    default_piece = "Knight"
    default_color = default_colors[i % len(default_colors)]

    # ----------------------------------------
    # randomized values
    # ----------------------------------------

    if "randomized_pieces" in st.session_state:
        if i < len(st.session_state.randomized_pieces):
            default_piece = (
                st.session_state.randomized_pieces[i]
            )

    if "randomized_colors" in st.session_state:
        if i < len(st.session_state.randomized_colors):
            default_color = (
                st.session_state.randomized_colors[i]
            )

    # ----------------------------------------
    # widgets
    # ----------------------------------------

    piece = st.sidebar.selectbox(
        f"Piece {i+1}",
        list(PIECES.keys()),
        index=list(PIECES.keys()).index(default_piece),
        key=f"p{i}_{st.session_state.random_seed}",
    )

    color = st.sidebar.color_picker(
        f"Color {i+1}",
        value=default_color,
        key=f"c{i}_{st.session_state.random_seed}",
    )

    configs.append({
        "piece": piece,
        "color": hex_to_rgb(color),
    })


players = []
for i, c in enumerate(configs):
    players.append({
        "id": i,
        "mask": 1 << i,
        "moves": PIECES[c["piece"]],
        "color": c["color"],
        "x": 0,
        "y": 0,
    })


# ============================================================
# SIMULATION (RUN ONCE)
# ============================================================

occupied = set()
attack_map = defaultdict(int)

positions = []
frames = []

counter = 0
frame_interval = max(1, (turns * num_players) // (10 * fps))

progress = st.progress(0)

for t in range(turns):

    order = players.copy()
    if turn_mode == "Random":
        random.shuffle(order)

    for p in order:

        x, y = p["x"], p["y"]
        mask = p["mask"]

        while True:
            key = encode(x, y)

            if key not in occupied:
                if attack_map.get(key, 0) & ~mask == 0:
                    break

            x, y = spiral_move(x, y)

        occupied.add(key)

        p["x"], p["y"] = x, y
        positions.append((x, y, p["color"]))

        for dx, dy in p["moves"]:
            attack_map[encode(x+dx, y+dy)] |= mask

        counter += 1

        if make_animation and counter % frame_interval == 0:

            coords = np.array([[a,b] for a,b,_ in positions])
            half = max(1, int(np.max(np.abs(coords))))
            size = 2*half + 1

            img = np.empty((size,size,3), dtype=np.uint8)
            img[:,:] = bg

            for x,y,c in positions:
                img[half-y, half+x] = c
            pil_frame = Image.fromarray(img) 
            pil_frame = pil_frame.resize( (GIF_SIZE, GIF_SIZE), Image.Resampling.NEAREST, )

            frames.append(pil_frame)

    if t % 1000 == 0:
        progress.progress(t / turns)

progress.empty()


# ============================================================
# FINAL IMAGE
# ============================================================

coords = np.array([[x,y] for x,y,_ in positions])
half = max(1, int(np.max(np.abs(coords))))
size = 2*half + 1

img = np.empty((size,size,3), dtype=np.uint8)
img[:,:] = bg

for x,y,c in positions:
    img[half-y, half+x] = c

final_img = Image.fromarray(img)

st.subheader("Final State")
st.image(final_img, use_container_width=True)


# ============================================================
# GIF EXPORT (RESTORED CLEAN VERSION)
# ============================================================
def crop_center(img, size=480):
    w, h = img.size

    left = (w - size) // 2
    top = (h - size) // 2
    right = left + size
    bottom = top + size

    return img.crop((left, top, right, bottom))

def make_gif(frames, fps):
    buf = io.BytesIO()
    durations = [ int(1000 / fps) for _ in range(len(frames)) ] # final frame lingers 1 second durations[-1] = 1000
    durations[-1] = 1000

    cropped = [
        crop_center(f, 480)
        for f in frames
    ]

    cropped[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=cropped[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )

    return buf.getvalue()


if make_animation and len(frames) > 1:

    st.subheader("Export")

    gif_bytes = make_gif(frames, fps)

    st.download_button(
        "Download GIF",
        data=gif_bytes,
        file_name="spiral_growth.gif",
        mime="image/gif",
    )


# ============================================================
# REAL SMOOTH PLAYER (JS FRONTEND)
# ============================================================

if make_animation and len(frames) > 1:

    st.subheader("Smooth Viewer (No Lag)")

    # encode frames as base64 PNG list
    encoded_frames = []
    for f in frames:
        buf = io.BytesIO()
        f.save(buf, format="PNG")
        encoded_frames.append(
            base64.b64encode(buf.getvalue()).decode()
        )

    html = f"""
    <div style="text-align:center;">
        <img id="frame" style="width:100%; max-width:500px; image-rendering:pixelated;">

        <br><br>

        <input type="range" min="0" max="{len(encoded_frames)-1}"
               value="0" id="slider" style="width:500px;"/>

        <button onclick="playing = !playing;">Play/Pause</button>
    </div>

    <script>
        let frames = {encoded_frames};
        let i = 0;
        let playing = false;

        const img = document.getElementById("frame");
        const slider = document.getElementById("slider");

        function render(idx) {{
            img.src = "data:image/png;base64," + frames[idx];
        }}

        slider.oninput = (e) => {{
            i = parseInt(e.target.value);
            render(i);
        }}

        function loop() {{
            if (playing) {{
                i = (i + 1) % frames.length;
                slider.value = i;
                render(i);
            }}
        }}

        setInterval(loop, {int(1000/fps)});
        render(0);
    </script>
    """

    st.components.v1.html(html, height=650)
