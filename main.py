import os
import duckdb

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

# ============================================================
# DUCKDB
# ============================================================

con = duckdb.connect()

con.execute("INSTALL httpfs;")
con.execute("LOAD httpfs;")


# ============================================================
# HUGGING FACE
# ============================================================

HF_TOKEN = os.getenv("HF_TOKEN")

if HF_TOKEN:
    con.execute(
        f"CREATE OR REPLACE SECRET hf_secret ("
        f"TYPE HUGGINGFACE, "
        f"TOKEN '{HF_TOKEN}'"
        f")"
    )


BUCKET = "hf://buckets/CutehackX/hitek-data-bucket"


# ============================================================
# LANDING PAGE
# ============================================================

LANDING_PAGE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Hitek Data Gateway - LIVE</title>

<style>

body {
    margin: 0;
    overflow: hidden;
    background: #050505;
    color: #00ffcc;
    font-family: "Courier New", monospace;
}

#canvas-container {
    position: absolute;
    inset: 0;
    z-index: -1;
}

.overlay {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);

    text-align: center;

    background: rgba(10, 10, 10, 0.85);

    padding: 50px;

    border: 1px solid #00ffcc;
    border-radius: 12px;

    box-shadow:
        0 0 30px rgba(0, 255, 204, 0.3);

    backdrop-filter: blur(5px);
}

h1 {
    margin: 0 0 15px 0;

    font-size: 3.5em;

    text-transform: uppercase;

    letter-spacing: 6px;

    text-shadow:
        0 0 15px #00ffcc;
}

p {
    font-size: 1.2em;
    margin: 8px 0;
    color: #ccc;
}

.highlight {
    color: #00ffcc;
    font-weight: bold;
}

.status-box {
    margin-top: 30px;

    font-weight: bold;

    padding: 15px;

    border-radius: 8px;

    background: rgba(0, 255, 204, 0.1);

    border: 1px solid rgba(0, 255, 204, 0.5);

    font-size: 1.1em;
}

.blinking {
    animation: blinker 1.5s linear infinite;
}

@keyframes blinker {
    50% {
        opacity: 0;
    }
}

</style>
</head>

<body>

<div id="canvas-container"></div>

<div class="overlay">

<h1>SYSTEM ONLINE</h1>

<p>
API Gateway is
<span class="highlight">
Active & Secured
</span>
</p>

<p>
Parquet Cloud Engine:
<span class="highlight">
Connected
</span>
</p>

<div class="status-box">

<span class="blinking">
●
</span>

HTTP 200 OK - LISTENING FOR QUERIES

</div>

</div>


<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>

<script>

const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(
    75,
    window.innerWidth / window.innerHeight,
    0.1,
    2000
);

const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true
});

renderer.setSize(
    window.innerWidth,
    window.innerHeight
);

document
    .getElementById("canvas-container")
    .appendChild(renderer.domElement);


const geometry = new THREE.BufferGeometry();

const vertices = [];

for (let i = 0; i < 8000; i++) {

    vertices.push(
        THREE.MathUtils.randFloatSpread(3000)
    );

    vertices.push(
        THREE.MathUtils.randFloatSpread(3000)
    );

    vertices.push(
        THREE.MathUtils.randFloatSpread(3000)
    );
}

geometry.setAttribute(
    "position",
    new THREE.Float32BufferAttribute(vertices, 3)
);


const material = new THREE.PointsMaterial({
    color: 0x00ffcc,
    size: 2.5,
    transparent: true,
    opacity: 0.8
});


const points = new THREE.Points(
    geometry,
    material
);

scene.add(points);

camera.position.z = 1200;


function animate() {

    requestAnimationFrame(animate);

    points.rotation.x += 0.0005;
    points.rotation.y += 0.001;

    renderer.render(scene, camera);
}

animate();


window.addEventListener("resize", () => {

    camera.aspect =
        window.innerWidth /
        window.innerHeight;

    camera.updateProjectionMatrix();

    renderer.setSize(
        window.innerWidth,
        window.innerHeight
    );

});

</script>

</body>
</html>
"""


# ============================================================
# ERROR HANDLER
# ============================================================

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
):

    if exc.status_code == 404:

        return JSONResponse(
            status_code=404,
            content={
                "status": "rejected",
                "message": "Invalid endpoint. STRICTLY use /FetchData?Number=XXXXXXXXXX",
                "Developer": "@Maybechx"
            }
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "Developer": "@Maybechx"
        }
    )


# ============================================================
# HOME
# ============================================================

@app.get("/", response_class=HTMLResponse)
def root_landing_page():

    return HTMLResponse(
        content=LANDING_PAGE_HTML,
        status_code=200
    )


# ============================================================
# FETCH DATA
# ============================================================

@app.get("/FetchData")
def fetch_data(
    Number: str = Query(default=None)
):

    # --------------------------------------------------------
    # Validate Number
    # --------------------------------------------------------

    if (
        not Number
        or not Number.isdigit()
        or len(Number) < 10
        or len(Number) > 15
    ):

        return JSONResponse(
            status_code=400,
            content={
                "status": "rejected",
                "message": "Invalid parameter. STRICTLY use /FetchData?Number=XXXXXXXXXX",
                "Developer": "@Maybechx"
            }
        )


    # --------------------------------------------------------
    # Select shard
    # --------------------------------------------------------

    last_digit = Number[-1]


    primary_url = (
        f"{BUCKET}/"
        f"final_master_shard_{last_digit}.parquet"
    )

    alt_url = (
        f"{BUCKET}/"
        f"alt_master_shard_{last_digit}.parquet"
    )


    try:

        # ----------------------------------------------------
        # Main records
        # ----------------------------------------------------

        main_query = """
            SELECT *
            FROM read_parquet(?)
            WHERE CAST(mobile AS VARCHAR) = ?
        """

        main_results = con.execute(
            main_query,
            [
                primary_url,
                Number
            ]
        ).fetchdf()


        # ----------------------------------------------------
        # Alt records
        # ----------------------------------------------------

        alt_query = """
            SELECT *
            FROM read_parquet(?)
            WHERE CAST(alt AS VARCHAR) = ?
        """

        alt_results = con.execute(
            alt_query,
            [
                alt_url,
                Number
            ]
        ).fetchdf()


        # ----------------------------------------------------
        # Convert to JSON-compatible records
        # ----------------------------------------------------

        main_records = main_results.to_dict(
            orient="records"
        )

        alt_records = alt_results.to_dict(
            orient="records"
        )


        # ----------------------------------------------------
        # Not found
        # ----------------------------------------------------

        if not main_records and not alt_records:

            return JSONResponse(
                status_code=404,
                content={
                    "status": "not_found",
                    "phone": Number,
                    "Developer": "@Maybechx"
                }
            )


        # ----------------------------------------------------
        # Success
        # ----------------------------------------------------

        return {
            "status": "success",

            "Data": {
                "Main_Records": main_records,
                "Alt_Records": alt_records
            },

            "Developer": "@Maybechx"
        }


    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": (
                    "Database processing error: "
                    + str(e)
                ),
                "Developer": "@Maybechx"
            }
        )
