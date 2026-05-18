import io, time, os, random, math
import base64
from collections import defaultdict

import numpy as np
import streamlit as st
from PIL import Image
from numba import njit




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

@njit
def square_cw_0(x, y, t):
    w = max(abs(x), abs(y))

    if y == -w:
        return x + 1, y, t+1
    if x == -w:
        return x, y - 1, t+1
    if y == w:
        return x - 1, y, t+1

    return x, y + 1, t+1

@njit
def square_cw_1(x, y, t):
    w = max(abs(x), abs(y))

    if x == -w:
        return x, y - 1, t+1
    if y == w:
        return x - 1, y, t+1
    if x == w:
        return x, y + 1, t+1

    return x + 1, y, t+1

@njit
def square_cw_2(x, y, t):
    w = max(abs(x), abs(y))

    if y == w:
        return x - 1, y, t+1
    if x == w:
        return x, y + 1, t+1
    if y == -w:
        return x + 1, y, t+1

    return x, y - 1, t+1

@njit
def square_cw_3(x, y, t):
    w = max(abs(x), abs(y))

    if x == w:
        return x, y + 1, t+1
    if y == -w:
        return x + 1, y, t+1
    if x == -w:
        return x, y - 1, t+1

    return x - 1, y, t+1

@njit
def square_ccw_0(x, y, t):
    w = max(abs(x), abs(y))

    if y == -w:
        return x - 1, y, t+1
    if x == w:
        return x, y - 1, t+1
    if y == w:
        return x + 1, y, t+1

    return x, y + 1, t+1

@njit
def square_ccw_1(x, y, t):
    w = max(abs(x), abs(y))

    if x == -w:
        return x, y + 1, t+1
    if y == -w:
        return x - 1, y, t+1
    if x == w:
        return x, y - 1, t+1

    return x + 1, y, t+1

@njit
def square_ccw_2(x, y, t):
    w = max(abs(x), abs(y))

    if y == w:
        return x + 1, y, t+1
    if x == -w:
        return x, y + 1, t+1
    if y == -w:
        return x - 1, y, t+1

    return x, y - 1, t+1

@njit
def square_ccw_3(x, y, t):
    w = max(abs(x), abs(y))

    if x == w:
        return x, y - 1, t+1
    if y == w:
        return x + 1, y, t+1
    if x == -w:
        return x, y + 1, t+1

    return x - 1, y, t+1

@njit
def fermat_move(x, y, t):
    a = 1.5

    theta = t * 0.2
    r = math.sqrt(a * a * theta)

    nx = int(round(r * math.cos(theta)))
    ny = int(round(r * math.sin(theta)))

    return nx, ny, t + 1
@njit
def archimedean_move(x, y, t):
    a = 1
    b = 0.02

    theta=t*.005
    r = a + b * theta

    nx = int(round(r * math.cos(theta)))
    ny = int(round(r * math.sin(theta)))

    return nx, ny, t + 1

@njit
def double_move(x, y, t):

    # base spiral
    theta = t * 0.001
    r = 0.05 * theta

    # two arms: phase shift π
    if t % 2 == 0:
        offset = 0
    else:
        offset = np.pi

    nx = int(round(r * math.cos(theta + offset)))
    ny = int(round(r * math.sin(theta + offset)))

    return nx, ny, t + 1

@njit
def log_move(x, y, t):
    a = 1
    b = 0.015

    theta = t * 0.005
    r = (1.15)**(b*theta)

    nx = int(round(r * math.cos(theta)))
    ny = int(round(r * math.sin(theta)))

    return nx, ny, t + 1

@njit
def phyllotaxis_move(x, y, t):
    c = 0.12
    golden_angle = np.deg2rad(137.5)

    theta = t * golden_angle*0.01
    r = c * math.sqrt(t)

    nx = int(round(r * math.cos(theta)))
    ny = int(round(r * math.sin(theta)))

    return nx, ny, t + 1

@njit
def triangle_move(x, y, t):
    k = t % 3
    tri_angle = 2 * np.pi / 3

    # smooth outward growth
    r = 0.001 * t

    # rotate base angle slowly + snap into 5 symmetry phases
    theta = (t * 0.005) + (k * tri_angle)

    nx = int(round(r * math.cos(theta)))
    ny = int(round(r * math.sin(theta)))

    return nx, ny, t + 1

@njit
def pentagon_move(x, y, t):
    # 5-fold symmetry
    k = t % 5
    golden_angle = 2 * np.pi / 5

    # smooth outward growth
    r = 0.001 * t

    # rotate base angle slowly + snap into 5 symmetry phases
    theta = (t * 0.005) + (k * golden_angle)

    nx = int(round(r * math.cos(theta)))
    ny = int(round(r * math.sin(theta)))

    return nx, ny, t + 1

@njit
def star_move(x, y, t):
    # 5-point star vertices (unit directions)
    # star connection order (THIS is key)
    order = [0, 2, 4, 1, 3]

    cycle_len = 5
    k = t % cycle_len

    # growth only after full star is drawn
    #r = 1 + 0.5 * cycle
    r = 0.001 * t
    theta = (t * 0.005) + order[k]*(2 * np.pi / 5)

    nx = int(round(r * math.cos(theta)))
    ny = int(round(r * math.sin(theta)))

    return nx, ny, t + 1

def random_polygon_move(x, y, t):

    # random order of 5 vertices
    order = st.session_state.random_polygon_order

    cycle_len = 5
    k = t % cycle_len

    r = 0.001 * t

    theta = (t * 0.005) + order[k] * (2 * np.pi / 5)

    nx = int(round(r * math.cos(theta)))
    ny = int(round(r * math.sin(theta)))

    return nx, ny, t + 1

@njit
def hexagon_move(x, y, t):
    k = t % 6
    hex_angle = 2 * np.pi / 6

    # smooth outward growth
    r = 0.001 * t

    # rotate base angle slowly + snap into 5 symmetry phases
    theta = (t * 0.005) + (k * hex_angle)

    nx = int(round(r * math.cos(theta)))
    ny = int(round(r * math.sin(theta)))

    return nx, ny, t + 1

@njit
def hexagram_move(x, y, t):
    # star connection order (THIS is key)
    #order = [2,0,3,5,1,4]
    order = [0,3,5,1,4,2,]
    cycle_len = 6
    k = t % cycle_len

    # growth only after full star is drawn
    #r = 1 + 0.5 * cycle
    r = 0.001 * t
    theta = (t * 0.005) + order[k]*(2 * np.pi / 6)

    nx = int(round(r * math.cos(theta)))
    ny = int(round(r * math.sin(theta)))

    return nx, ny, t + 1

@njit
def ribbonhex_move(x, y, t):
    # star connection order (THIS is key)
    order = [2,0,1,5,3,4]

    cycle_len = 6
    k = t % cycle_len

    # growth only after full star is drawn
    #r = 1 + 0.5 * cycle
    r = 0.001 * t
    theta = (t * 0.005) + order[k]*(2 * np.pi / 6)

    nx = int(round(r * math.cos(theta)))
    ny = int(round(r * math.sin(theta)))

    return nx, ny, t + 1

def random_hexagon_move(x, y, t):

    # random order of 5 vertices
    order = st.session_state.random_hexagon_order

    cycle_len = 6
    k = t % cycle_len

    r = 0.001 * t

    theta = (t * 0.005) + order[k] * (2 * np.pi / 6)

    nx = int(round(r * math.cos(theta)))
    ny = int(round(r * math.sin(theta)))

    return nx, ny, t + 1

@njit
def lissajous_move(x,y,t):
    cycle = t // 330
    a = 2
    b = 3

    theta = t*.02
    r =  (1 if cycle % 2 == 0 else -1)*math.sqrt(cycle + 1)

    x = int(round(r * math.sin(a * theta)))
    y = int(round(r * math.sin(b * theta)))

    # Turn sideways every cycle
    if cycle % 4 == 1:
        x, y = y, x 
    if cycle % 4 == 2:
        x, y = x, -y 
    if cycle % 4 == 3:
        x, y = -y, x

    return x, y,t+1

@njit
def rose_move(x,y,t):

    k = 5
    cycle = t // 220
    theta = t * 0.015 

    r = math.sqrt(cycle + 1) * math.cos(k * theta)

    x = int(round(r * math.cos(theta+ cycle*np.pi/20)))
    y = int(round(r * math.sin(theta+ cycle*np.pi/20)))

    return x, y, t+1

@njit
def harmonic_move(x,y,t):

    theta = t * .15
    cycle = t//200

    r = math.sqrt(cycle + 1)*math.sin(theta * 0.3)+ 0.001 * t

    x = int(round(r * math.cos(theta/30)))
    y = int(round(r * math.sin(theta/30)))

    return x, y, t+1

@njit
def lemniscate_move(x,y,t):
    cycle = t // 157

    theta = t * 0.04

    r = math.sqrt(
        abs(math.cos(2*theta))
    ) * math.sqrt(cycle + 1)

    x = int(round(r * math.cos(theta)))
    y = int(round(r * math.sin(theta)))

    if cycle % 4 == 1:
        x, y = y, x 
    if cycle % 4 == 2:
        x, y = x, -y 
    if cycle % 4 == 3:
        x, y = -y, x

    return x, y, t+1

def binary_move(x,y,t):
    theta = t * 0.08
    t2=math.sqrt(t)
    cycle = t // 70
    
    if t % 2 == 0:
        r = 0.05*(2 + 0.06*t2+cycle)
    else:
        r = 0.05*(3 + 0.06*t2+cycle)

    x = int(round(r * math.cos(theta)))
    y = int(round(r * math.sin(theta)))

    return x, y, t+1

@njit
def moire_move(x,y,t):

    theta = t * 0.05
    t2=math.sqrt(t)

    r = 0.5*(
        t2
        + 6*math.sin(theta*3.1)
    )

    x = int(round(r * math.cos(theta)))
    y = int(round(r * math.sin(theta)))

    return x, y, t+1

def hex_to_rgb(h):
    h = h.lstrip("#")
    return np.array([
        int(h[0:2], 16),
        int(h[2:4], 16),
        int(h[4:6], 16),
    ], dtype=np.uint8)

SQUARE_VARIANTS = [
    square_cw_0,
    square_cw_1,
    square_cw_2,
    square_cw_3,
    square_ccw_0,
    square_ccw_1,
    square_ccw_2,
    square_ccw_3,
]

if "random_square_variant" not in st.session_state:
        st.session_state.random_square_variant = random.choice(
            SQUARE_VARIANTS
        )
if "random_polygon_order" not in st.session_state:
        st.session_state.random_polygon_order = (
            random.sample(range(5), 5)
        )
if "random_hexagon_order" not in st.session_state:
        st.session_state.random_hexagon_order = (
            random.sample(range(6), 6)
        )


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
    "Mastodon": [(-5,8),(5,8),(-8,5),(8,5),(-8,-5),(8,-5),(5,-8),(-5,-8)],
    "Auroch": [(-2,5),(2,5),(-5,2),(5,2),(-5,-2),(5,-2),(2,-5),(-2,-5)],
    "Qilin": [(-1,5),(1,5),(-5,1),(5,1),(-5,-1),(5,-1),(1,-5),(-1,-5)],
    "Moriana": [(-4,5),(4,5),(-5,4),(5,4),(-5,-4),(5,-4),(4,-5),(-4,-5)],
}


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Simulation")

num_players = st.sidebar.slider("Players", 1, 8, 3)
turns = st.sidebar.slider("Turns", 100, 1000000, 10000, step=100)

bg = hex_to_rgb(st.sidebar.color_picker("Background", "#FFFFFF"))

turn_mode = st.sidebar.selectbox("Turn Order", ["Cyclic", "Random"])

# ============================================================
# SPIRAL SELECTOR
# ============================================================

SPIRALS = {
    "Square": square_cw_0,
    "Fermat": fermat_move,
    "Archimedean": archimedean_move,
    "Double": double_move,
    "Log": log_move,
    "Phyllotaxis": phyllotaxis_move,
    "Triangle": triangle_move,
    "Pentagon": pentagon_move,
    "Star": star_move,
    "Random Polygon": random_polygon_move,
    "Hexagon": hexagon_move,
    "Hexagram": hexagram_move,
    "Ribbon Hex": ribbonhex_move,
    "Random Hexagon": random_hexagon_move,
    "Lissajous": lissajous_move,
    "Rose": rose_move,
    "Harmonic": harmonic_move,
    "Lemniscate": lemniscate_move,
    "Binary": binary_move,
    "Moire": moire_move,
    "Random Square": "Random Square",
}

same_spiral = st.sidebar.checkbox(
    "Shared Spiral",
    value=True,
)

global_spiral_name = None

if same_spiral:

    global_spiral_name = st.sidebar.selectbox(
        "Shared Spiral",
        list(SPIRALS.keys()),
    )

    # detect spiral change
    if "last_spiral" not in st.session_state:
        st.session_state.last_spiral = global_spiral_name

    # regenerate random orders ONLY on change
    if global_spiral_name != st.session_state.last_spiral:

        st.session_state.random_polygon_order = (
            random.sample(range(5), 5)
        )

        st.session_state.random_hexagon_order = (
            random.sample(range(6), 6)
        )

        st.session_state.random_square_variant = random.choice(
            SQUARE_VARIANTS
        )

        st.session_state.last_spiral = global_spiral_name

# spiral_name = st.sidebar.selectbox(
#     "Spiral",
#     list(SPIRALS.keys()),
# )

# # detect spiral change
# if "last_spiral" not in st.session_state:
#     st.session_state.last_spiral = spiral_name

# # generate new random polygon order
# # ONLY when spiral changes
# if spiral_name != st.session_state.last_spiral:

#     st.session_state.random_polygon_order = (
#         random.sample(range(5), 5)
#     )
#     st.session_state.random_hexagon_order = (
#         random.sample(range(6), 6)
#     )


#     st.session_state.last_spiral = spiral_name

# # initialize once
# if "random_polygon_order" not in st.session_state:
#     st.session_state.random_polygon_order = (
#         random.sample(range(5), 5)
#     )

# # initialize once
# if "random_hexagon_order" not in st.session_state:
#     st.session_state.random_hexagon_order = (
#         random.sample(range(6), 6)
#     )

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
    "#FFD700",  # gold
    "#8800FF",  # purple
    "#000000",  # black
    "#FF66AA",  # pink
    "#66FF66",  # lime
    "#AA5500",  # brown
    "#44FFDD",  # aqua
    "#FFFF00",  # yellow
    "#BA55D3",  # orchid
    "#DC143C",  # crimson
]
# ============================================================
# RANDOMIZE PLAYERS
# ============================================================

if "random_seed" not in st.session_state:
    st.session_state.random_seed = int(time.time() * 1000) ^ os.getpid()

rng = random.Random(
        st.session_state.random_seed
    )

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

    random_spirals = [
        rng.choice(list(SPIRALS.keys()))
        for _ in range(num_players)
    ]

    st.session_state.randomized_colors = shuffled_colors
    st.session_state.randomized_pieces = random_pieces
    st.session_state.randomized_spirals = random_spirals

configs = []
for i in range(num_players):

    st.sidebar.subheader(f"Player {i+1}")

    # ----------------------------------------
    # defaults
    # ----------------------------------------

    default_piece = "Knight"
    default_color = default_colors[i % len(default_colors)]
    default_spiral = list(SPIRALS.keys())[0]

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

    if "randomized_spirals" in st.session_state:
        if i < len(st.session_state.randomized_spirals):
            default_spiral = (
                st.session_state.randomized_spirals[i]
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

    if same_spiral:

        spiral_choice = global_spiral_name

    else:

        spiral_choice = st.sidebar.selectbox(
            f"Spiral {i+1}",
            list(SPIRALS.keys()),
            index=list(SPIRALS.keys()).index(default_spiral),
            key=f"spiral_{i}_{st.session_state.random_seed}",
        )

    configs.append({
        "piece": piece,
        "color": hex_to_rgb(color),
        "spiral": spiral_choice,
    })


players = []
for i, c in enumerate(configs):
    spiral_name = c["spiral"]
    if spiral_name == "Random Square":
        if(same_spiral):
            spiral_func = st.session_state.random_square_variant
        else:
            spiral_func = random.choice(SQUARE_VARIANTS)
    else:
        spiral_func = SPIRALS[spiral_name]

    players.append({
        "id": i,
        "mask": 1 << i,
        "moves": PIECES[c["piece"]],
        "color": c["color"],
        "spiral": spiral_func,
        "x": 0,
        "y": 0,
        "t": 0,
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

for tu in range(turns):

    order = players.copy()
    if turn_mode == "Random":
        random.shuffle(order)

    for p in order:

        x, y, t = p["x"], p["y"], p["t"]
        mask = p["mask"]

        while True:
            key = encode(x, y)

            if key not in occupied:
                if attack_map.get(key, 0) & ~mask == 0:
                    break

            x, y, t = p["spiral"](x, y, t)

        occupied.add(key)

        p["x"], p["y"], p["t"] = x, y, t
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

    if tu % 1000 == 0:
        progress.progress(tu / turns)

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
