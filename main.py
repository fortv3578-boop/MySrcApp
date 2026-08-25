from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import duckdb

app = FastAPI()

# --------------------------------------------------
# DuckDB
# --------------------------------------------------

con = duckdb.connect()

con = duckdb.connect()

con.execute("INSTALL httpfs;")
con.execute("LOAD httpfs;")

# Test/fix HTTP certificate handling
con.execute("SET enable_server_cert_verification = false;")

print("DuckDB version:", con.execute("SELECT version()").fetchone()[0])
print("httpfs loaded successfully")
# --------------------------------------------------
# Configuration
# --------------------------------------------------

DATASET_OWNER = "CutehackX"
DATASET_NAME = "hitek-data-bucket"

# --------------------------------------------------
# Landing page
# --------------------------------------------------

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
            background-color: #050505;
            color: #00ffcc;
            font-family: 'Courier New', Courier, monospace;
        }

        #canvas-container {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
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
            box-shadow: 0 0 30px rgba(0, 255, 204, 0.3);
            backdrop-filter: blur(5px);
        }

        h1 {
            margin: 0 0 15px 0;
            font-size: 3.5em;
            text-transform: uppercase;
            letter-spacing: 6px;
            text-shadow: 0 0 15px #00ffcc;
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
            display: inline-block;
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
        <span class="highlight">Active & Secured</span>
    </p>

    <p>
        Parquet Cloud Engine:
        <span class="highlight">Connected</span>
    </p>

    <div class="status-box">
        <span class="blinking" style="color: #00ffcc;">●</span>
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
        .getElementById('canvas-container')
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
        'position',
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

    window.addEventListener('resize', () => {
        camera.aspect =
            window.innerWidth / window.innerHeight;

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

# --------------------------------------------------
# Error handler
# --------------------------------------------------

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
                "message": "Invalid endpoint.",
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


# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def root_landing_page():
    return HTMLResponse(
        content=LANDING_PAGE_HTML,
        status_code=200
    )


# --------------------------------------------------
# Test endpoint
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "database": "DuckDB",
        "engine": "httpfs",
        "Developer": "@Maybechx"
    }
@app.get("/TestHuggingFace")
def test_huggingface():
    urls = [
        "https://huggingface.co/datasets/CutehackX/hitek-data-bucket/resolve/main/final_master_shard_0.parquet",
        "hf://datasets/CutehackX/hitek-data-bucket/final_master_shard_0.parquet"
    ]

    results = []

    for url in urls:
        try:
            result = con.execute(
                "SELECT COUNT(*) FROM read_parquet(?)",
                [url]
            ).fetchone()

            results.append({
                "url": url,
                "status": "success",
                "rows": result[0]
            })

        except Exception as e:
            results.append({
                "url": url,
                "status": "error",
                "error": str(e)
            })

    return {
        "status": "test_complete",
        "results": results
            }

# --------------------------------------------------
# Parquet lookup
# --------------------------------------------------

@app.get("/FetchData")
def fetch_data(
    Number: str = Query(None)
):
    if not Number:
        return JSONResponse(
            status_code=400,
            content={
                "status": "rejected",
                "message": "Missing Number parameter.",
                "Developer": "@Maybechx"
            }
        )

    # Generic validation for a non-sensitive identifier.
    if not Number.isalnum():
        return JSONResponse(
            status_code=400,
            content={
                "status": "rejected",
                "message": "Invalid identifier.",
                "Developer": "@Maybechx"
            }
        )

    # --------------------------------------------------
    # Select shard
    # --------------------------------------------------

    last_digit = Number[-1]

    primary_url = (
        f"hf://datasets/{DATASET_OWNER}/{DATASET_NAME}/"
        f"final_master_shard_{last_digit}.parquet"
    ).strip()

    alt_url = (
        f"hf://datasets/{DATASET_OWNER}/{DATASET_NAME}/"
        f"alt_master_shard_{last_digit}.parquet"
    ).strip()

    print("PRIMARY URL:", repr(primary_url))
    print("ALT URL:", repr(alt_url))

    # --------------------------------------------------
    # Query
    # --------------------------------------------------

    try:

        # Parameterized values avoid injecting the identifier
        # directly into the SQL statement.

        query = f"""
            SELECT *,
                   'Main' AS _record_type
            FROM read_parquet(?)

            UNION ALL

            SELECT *,
                   'Alt' AS _record_type
            FROM read_parquet(?)
        """

        raw_results = con.execute(
            query,
            [
                primary_url,
                alt_url
            ]
        ).df().to_dict(
            orient="records"
        )

        # --------------------------------------------------
        # Separate result types
        # --------------------------------------------------

        main_records = []
        alt_records = []

        for row in raw_results:

            rec_type = row.pop(
                "_record_type",
                None
            )

            if rec_type == "Main":
                main_records.append(row)

            elif rec_type == "Alt":
                alt_records.append(row)

        # --------------------------------------------------
        # No results
        # --------------------------------------------------

        if not main_records and not alt_records:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "not_found",
                    "Developer": "@Maybechx"
                }
            )

        # --------------------------------------------------
        # Success
        # --------------------------------------------------

        return {
            "status": "success",
            "Data": {
                "Main_Records": main_records,
                "Alt_Records": alt_records
            },
            "Developer": "@Maybechx"
        }

    # --------------------------------------------------
    # Database error
    # --------------------------------------------------

    except Exception as e:

        print(
            "DATABASE ERROR:",
            repr(e)
        )

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Database processing error: {str(e)}",
                "Developer": "@Maybechx"
            }
        )
