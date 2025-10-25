# Road Connectivity Analysis Web App

This project is a **Flask-based web application** for analyzing and visualizing road network connectivity from shapefiles. The tool allows users to upload a ZIP file containing road shapefile data, computes node connectivity using NetworkX and GeoPandas, and displays the results on an interactive Leaflet map.

---

## 🚀 Features

* Upload `.zip` shapefile of road networks
* Automatically extracts, processes, and computes network connectivity
* Generates and downloads processed outputs:

  * GeoJSON file (visualization)
  * Shapefile (connectivity results)
* Interactive map visualization using **Leaflet.js**
* Color-coded nodes based on connectivity levels
* Built with **Flask**, **GeoPandas**, **NetworkX**, and **Leaflet**

---

## 🧩 Project Structure

```
project/
├─ app.py                   # Flask backend
├─ requirements.txt         # Python dependencies
├─ render.yaml              # Render deployment config
├─ templates/
│  └─ index.html            # Frontend HTML
├─ static/
│  ├─ styles.css            # CSS styling
│  └─ main.js               # JavaScript (Leaflet map + logic)
└─ outputs/                 # Auto-created for temporary results
```

---

## ⚙️ Local Development Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/<your-username>/road-connectivity-app.git
cd road-connectivity-app
```

### 2️⃣ (Optional) Create a Virtual Environment

```bash
conda create -n roadapp python=3.11
conda activate roadapp
```

Or using `venv`:

```bash
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run the App Locally

```bash
python app.py
```

Then visit: [**http://localhost:5000**](http://localhost:5000) 🌐

---

## ☁️ Deployment on Render

You can deploy this app on [Render](https://render.com) easily.

### Option 1: **GitHub Deployment (Recommended)**

1. Push your project to a GitHub repository.
2. Go to [Render.com](https://render.com) → **New + → Web Service**.
3. Connect your GitHub account and select your repo.
4. Set the following:

   * **Environment:** Python
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn app:app`
   * **Root Directory:** `.`
   * **Instance Type:** Free
5. Click **Deploy Web Service** ✅

Render will automatically detect your code and start the deployment. Each time you push changes to GitHub, Render will rebuild and redeploy automatically.

### Option 2: **Manual ZIP Upload**

1. Zip your project folder (including `app.py`, `templates/`, `static/`, etc.)
2. On Render → **New + → Web Service → Upload from ZIP**
3. Use the same settings as above.

---

## 🧠 Common Issues

### 1️⃣ CSS/JS Not Updating After Deployment

Browsers often cache static files. To force refresh, press **Ctrl + F5** or use a version query in `index.html`:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='styles.css?v=2') }}">
```

### 2️⃣ Missing Dependencies

If you see errors related to GeoPandas or Fiona on Render, try this `buildCommand` in your `render.yaml`:

```yaml
buildCommand: apt-get update && apt-get install -y gdal-bin python3-gdal && pip install -r requirements.txt
```

### 3️⃣ Large Files

Render free tier limits uploads. Make sure your shapefile ZIP is under 100MB.

---

## 📦 Requirements

```
Flask
geopandas
networkx
shapely
numpy
fiona
pyproj
gunicorn
```

---

## 🧾 License

This project is open source under the **MIT License**.

---

## 👨‍💻 Author

Developed by **Thimira Pradeep **
📍 Urban and Regional Planning Student
💡 Designed for analyzing road network connectivity in urban planning contexts.
