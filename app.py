import os
import tempfile
import zipfile
import shutil
import json
from io import BytesIO
from flask import Flask, request, render_template, jsonify, send_file, abort, url_for
import geopandas as gpd
import networkx as nx
import numpy as np
from shapely.geometry import Point

app = Flask(__name__)
WORKDIR = os.path.abspath(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(WORKDIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_shapefile_from_zip(zip_bytes, out_dir):
    with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
        shp_names = [n for n in zf.namelist() if n.lower().endswith(".shp")]
        if not shp_names:
            raise ValueError("No .shp file found inside the zip.")
        shp_member = shp_names[0]
        allowed_exts = {".shp", ".shx", ".dbf", ".prj", ".cpg", ".qpj", ".sbx", ".sbn"}
        for member in zf.namelist():
            _, ext = os.path.splitext(member)
            ext = ext.lower()
            if ext in allowed_exts:
                target_name = "roads_axial_lines" + ext
                target_path = os.path.join(out_dir, target_name)
                with zf.open(member) as source, open(target_path, "wb") as dest:
                    shutil.copyfileobj(source, dest)
        shp_path = os.path.join(out_dir, "roads_axial_lines.shp")
        if not os.path.exists(shp_path):
            raise ValueError("Failed to extract shapefile components correctly.")
        return shp_path


def compute_connectivity(shp_path):
    roads = gpd.read_file(shp_path)
    G = nx.Graph()

    endpoints = []
    for geom in roads.geometry:
        if geom is None:
            continue
        try:
            coords = list(geom.coords)
            endpoints.append(Point(coords[0]))
            endpoints.append(Point(coords[-1]))
        except Exception:
            for part in geom:
                coords = list(part.coords)
                endpoints.append(Point(coords[0]))
                endpoints.append(Point(coords[-1]))

    unique_nodes = {}
    for p in endpoints:
        key = (round(float(p.x), 6), round(float(p.y), 6))
        unique_nodes.setdefault(key, p)

    coord_to_node = {}
    for idx, (coord, pt) in enumerate(unique_nodes.items()):
        G.add_node(idx, geometry=pt)
        coord_to_node[coord] = idx

    for geom in roads.geometry:
        if geom is None:
            continue
        coords = []
        try:
            coords = list(geom.coords)
        except Exception:
            for part in geom:
                coords.extend(list(part.coords))
        if not coords:
            continue
        start = (round(coords[0][0], 6), round(coords[0][1], 6))
        end = (round(coords[-1][0], 6), round(coords[-1][1], 6))
        if start in coord_to_node and end in coord_to_node:
            G.add_edge(coord_to_node[start], coord_to_node[end])

    n = len(G.nodes())
    if n == 0:
        raise ValueError("No nodes found from the input roads.")

    dist_matrix = np.full((n, n), np.inf)
    for i in range(n):
        dist_matrix[i, i] = 0

    for i in G.nodes():
        lengths = nx.single_source_shortest_path_length(G, i)
        for j, L in lengths.items():
            dist_matrix[i, j] = L

    col_sums = dist_matrix.sum(axis=0)
    col_sums[col_sums == 0] = 1
    rel_matrix = dist_matrix / col_sums[np.newaxis, :]

    normalized_conn = rel_matrix.sum(axis=1)
    normalized_conn[normalized_conn == 0] = np.finfo(float).eps
    connectivity = 1.0 / normalized_conn

    rows = []
    for i, data in G.nodes(data=True):
        geom = data["geometry"]
        rows.append({
            "geometry": geom,
            "node_id": int(i),
            "normalized": float(normalized_conn[i]),
            "connectivity": float(connectivity[i])
        })

    nodes_gdf = gpd.GeoDataFrame(rows, crs=roads.crs if roads.crs else "EPSG:4326")
    try:
        nodes_gdf = nodes_gdf.to_crs("EPSG:4326")
    except Exception:
        pass
    return nodes_gdf


def save_shapefile_and_zip(gdf, out_prefix):
    tmp = tempfile.mkdtemp()
    shp_path = os.path.join(tmp, out_prefix + ".shp")
    gdf.to_file(shp_path)
    zip_path = os.path.join(OUTPUT_DIR, out_prefix + "_shp.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(tmp):
            if fname.startswith(out_prefix + "."):
                zf.write(os.path.join(tmp, fname), arcname=fname)
    shutil.rmtree(tmp)
    return zip_path


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"success": False, "error": "No selected file"}), 400

    contents = f.read()
    temp_dir = tempfile.mkdtemp()
    try:
        shp_path = extract_shapefile_from_zip(contents, temp_dir)

        roads = gpd.read_file(shp_path)
        try:
            roads_wgs = roads.to_crs("EPSG:4326")
        except Exception:
            roads_wgs = roads
        axial_geojson = json.loads(roads_wgs.to_json())

        nodes_gdf = compute_connectivity(shp_path)

        try:
            nodes_gdf = nodes_gdf.to_crs("EPSG:4326")
        except Exception:
            pass

        geojson_path = os.path.join(OUTPUT_DIR, "road_nodes_connectivity.geojson")
        nodes_gdf.to_file(geojson_path, driver="GeoJSON")

        shp_zip_path = save_shapefile_and_zip(nodes_gdf, "road_nodes_connectivity")

        with open(geojson_path, "r", encoding="utf-8") as gj:
            gj_text = gj.read()

        connectivity_vals = nodes_gdf["connectivity"].to_list()
        return jsonify({
            "success": True,
            "geojson_url": url_for("get_geojson"),
            "shp_zip_url": url_for("download_shp_zip"),
            "geojson": json.loads(gj_text),
            "axial_geojson": axial_geojson,
            "summary": {
                "count": len(nodes_gdf),
                "min_connectivity": min(connectivity_vals) if connectivity_vals else None,
                "max_connectivity": max(connectivity_vals) if connectivity_vals else None,
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.route("/outputs/road_nodes_connectivity.geojson")
def get_geojson():
    path = os.path.join(OUTPUT_DIR, "road_nodes_connectivity.geojson")
    if not os.path.exists(path):
        abort(404)
    return send_file(path, mimetype="application/geo+json")


@app.route("/outputs/road_nodes_connectivity_shp.zip")
def download_shp_zip():
    path = os.path.join(OUTPUT_DIR, "road_nodes_connectivity_shp.zip")
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name="road_nodes_connectivity_shp.zip")


@app.route("/outputs/road_nodes_connectivity.geojson/download")
def download_geojson():
    path = os.path.join(OUTPUT_DIR, "road_nodes_connectivity.geojson")
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name="road_nodes_connectivity.geojson")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
