let map = null;
let pointsLayer = null;
let axialLayer = null;
let geojsonData = null;

const uploadForm = document.getElementById("upload-form");
const shpInput = document.getElementById("shpzip");
const actions = document.getElementById("actions");
const downloadShpBtn = document.getElementById("download-shp");
const downloadGeoBtn = document.getElementById("download-geojson");
const summaryDiv = document.getElementById("summary");
const resetBtn = document.getElementById("reset-file");
const resetMsg = document.getElementById("reset-message");

let legend = null; // legend control reference

// Disable download buttons initially
downloadShpBtn.disabled = true;
downloadShpBtn.classList.add("bg-gray-400", "cursor-not-allowed");
downloadGeoBtn.disabled = true;
downloadGeoBtn.classList.add("bg-gray-400", "cursor-not-allowed");

function initMap() {
  map = L.map("map").setView([7.8731, 80.7718], 8); // Default Sri Lanka
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);
}

function stylePoints(feature, latlng) {
  const value = feature.properties.connectivity || 0;
  let color = "black";
  let radius = 4;

  if (value > 1.45) { color = "red"; radius = 12; }
  else if (value > 1.35) { color = "orange"; radius = 10; }
  else if (value > 1.25) { color = "lime"; radius = 8; }
  else if (value > 1.15) { color = "blue"; radius = 6; }
  else if (value > 1.05) { color = "magenta"; radius = 5; }

  return L.circleMarker(latlng, {
    radius: radius,
    color: color,
    weight: 1,
    fillOpacity: 0.8
  }).bindPopup(`Connectivity: ${value.toFixed(6)}`);
}

function styleAxialLines(feature) {
  return {
    color: "#003366",          // dark blue
    weight: 3,                  // thicker line
    opacity: 0.9,
    className: "axial-line"     // custom CSS class for glow
  };
}

function showGeoJSONOnMap(pointsGeoJSON, axialGeoJSON) {
  geojsonData = pointsGeoJSON;

  if (pointsLayer && map.hasLayer(pointsLayer)) {
    map.removeLayer(pointsLayer);
  }
  if (axialLayer && map.hasLayer(axialLayer)) {
    map.removeLayer(axialLayer);
  }

  if (axialGeoJSON) {
    axialLayer = L.geoJSON(axialGeoJSON, { style: styleAxialLines }).addTo(map);
  }

  pointsLayer = L.geoJSON(pointsGeoJSON, { pointToLayer: stylePoints }).addTo(map);

  try {
    let bounds = pointsLayer.getBounds();
    if (axialLayer) bounds.extend(axialLayer.getBounds());
    map.fitBounds(bounds, { maxZoom: 16 });
  } catch (err) {
    console.warn("No bounds available", err);
  }

  const overlays = {};
  if (axialLayer) overlays["Axial Lines"] = axialLayer;
  if (pointsLayer) overlays["Nodes"] = pointsLayer;

  if (map._layerControl) {
    map.removeControl(map._layerControl);
  }
  map._layerControl = L.control.layers(null, overlays, { collapsed: false }).addTo(map);

  if (legend) map.removeControl(legend);
  legend = L.control({ position: "bottomright" });
  legend.onAdd = function () {
    const div = L.DomUtil.create("div", "legend");
    div.innerHTML += "<b>Connectivity</b><br>";
    div.innerHTML += '<i style="background:red"></i> Very High (>1.45)<br>';
    div.innerHTML += '<i style="background:orange"></i> Fairly High (1.35–1.45)<br>';
    div.innerHTML += '<i style="background:lime"></i> Moderately High (1.25–1.35)<br>';
    div.innerHTML += '<i style="background:blue"></i> Moderately Low (1.15–1.25)<br>';
    div.innerHTML += '<i style="background:magenta"></i> Fairly Low (1.05–1.15)<br>';
    div.innerHTML += '<i style="background:black"></i> Very Low (<1.05)<br>';
    return div;
  };
  legend.addTo(map);
}

function showError(message) {
  summaryDiv.innerHTML = `<div class=\"error-message\">Error: ${message}</div>`;
}

uploadForm.addEventListener("submit", async (ev) => {
  ev.preventDefault();
  summaryDiv.innerHTML = "";
  if (!shpInput.files.length) {
    showError("No ZIP file selected. Please upload a ZIP file containing a shapefile.");
    return;
  }

  const file = shpInput.files[0];
  const formData = new FormData();
  formData.append("file", file);

  const submitBtn = uploadForm.querySelector("button[type=submit]");
  submitBtn.disabled = true;
  submitBtn.textContent = "Processing...";

  try {
    const resp = await fetch("/upload", { method: "POST", body: formData });
    const data = await resp.json();
    if (!data.success) {
      showError(data.error || "Unknown error occurred.");
      return;
    }

    showGeoJSONOnMap(data.geojson, data.axial_geojson || null);

    downloadShpBtn.disabled = false;
    downloadShpBtn.classList.remove("bg-gray-400", "cursor-not-allowed");
    downloadShpBtn.classList.add("bg-blue-500", "hover:bg-blue-700");

    downloadGeoBtn.disabled = false;
    downloadGeoBtn.classList.remove("bg-gray-400", "cursor-not-allowed");
    downloadGeoBtn.classList.add("bg-blue-500", "hover:bg-blue-700");

    actions.classList.remove("hidden");

    downloadShpBtn.onclick = () => { window.location = data.shp_zip_url; };
    downloadGeoBtn.onclick = () => { window.location = data.geojson_url + "/download"; };

    const minVal = data.summary.min_connectivity;
    const maxVal = data.summary.max_connectivity;

    summaryDiv.innerHTML = `
      <div><b>Nodes:</b> ${data.summary.count}</div>
      <div><b>Connectivity:</b> min ${minVal !== null ? minVal.toFixed(6) : "N/A"}, max ${maxVal !== null ? maxVal.toFixed(6) : "N/A"}</div>
    `;
  } catch (err) {
    console.error(err);
    showError("Upload/processing failed: " + err.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Upload & Run Analysis";
  }
});

resetBtn.addEventListener("click", () => {
  window.location.reload();
});

uploadForm.addEventListener("submit", () => {
  if (resetMsg) resetMsg.style.display = "none";
});

window.addEventListener("load", () => { initMap(); });

const style = document.createElement("style");
style.innerHTML = `
  .leaflet-interactive.axial-line {
    stroke: #003366;
    stroke-width: 0.75;
    filter: drop-shadow(0 0 10px rgba(1, 36, 78, 1));
  }
`;
document.head.appendChild(style);
