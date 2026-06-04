# 🏃‍♂️ Strava Performance Analytics

> **Complete ELT pipeline + Interactive Dashboard + Automated Reports for running and cycling performance analysis**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📋 About the Project

A complete **Data Science** and **Data Engineering** system that extracts, processes, and visualizes physical activity data from the **Strava API**. The project uses a modern ELT architecture to generate insights on athletic performance, including pace analysis, heart rate zones, GPS route maps, and Machine Learning predictions.

### 🎯 Main Features

- **Automated ELT pipeline** — Full extraction of historical activities via pagination
- **Relational database** — SQLite3 with 5 normalized and related tables
- **Interactive dashboard** — Streamlit with time filters, dynamic charts, and KPIs
- **GPS maps** — Route visualization with Folium and geospatial analysis
- **Advanced analysis** — Pace by distance (5K, 10K, 21K), HR zones, training volume
- **Automated reports** — Biweekly PDF sent by email with performance summary
- **Machine Learning** — Future time predictions based on historical data *(in development)*

---

## 🏗️ System Architecture

```
┌─────────────────┐
│   Strava API    │  ← OAuth 2.0 Authentication
└────────┬────────┘
         │ HTTP GET
         ↓
┌─────────────────┐
│  extract_load   │  ← ELT pipeline with pagination
│     (Python)    │     • activities (main table)
└────────┬────────┘     • activity_laps (km splits)
         │              • activity_zones (time in HR/power zones)
         ↓              • activity_streams (GPS time series)
┌─────────────────┐     • athlete (athlete profile)
│   SQLite3 DB    │
│   (strava.db)   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  transform.py   │  ← Transformations with Pandas
│   + Pandas      │     • Pace calculation (min/km)
└────────┬────────┘     • Time aggregations (weekly, monthly)
         │              • Feature engineering for ML
         ↓
┌─────────────────┐
│   Streamlit     │  ← Interactive Web Dashboard
│   Dashboard     │     • Charts: Plotly + Folium
└─────────────────┘     • Date / activity type filters
         │              • GPS map visualization
         ↓
┌─────────────────┐
│   PDF Report    │  ← Biweekly automation
│  + Email        │     • ReportLab (PDF generation)
└─────────────────┘     • Schedule (biweekly cron)
```

---

## 🗄️ Data Model

### Table Relationships

```sql
athlete (1) ──────< (N) activities
                           │
                           ├──────< (N) activity_laps
                           ├──────< (N) activity_zones
                           └──────< (N) activity_streams
```

### Schema Summary

| Table | Description | Key Fields |
|-------|-------------|------------|
| **athlete** | Athlete profile | `id`, `firstname`, `weight`, `ftp` |
| **activities** | Full activities | `id`, `name`, `distance`, `moving_time`, `average_heartrate` |
| **activity_laps** | Splits per km | `activity_id`, `lap_index`, `average_speed`, `average_heartrate` |
| **activity_zones** | Time in zones | `activity_id`, `zone_type`, `zone_index`, `time_in_zone` |
| **activity_streams** | GPS time series | `activity_id`, `time_seconds`, `lat`, `lng`, `heartrate` |

---

## 🚀 How to Run the Project

### Prerequisites

- Python 3.9+
- Account on [Strava Developers](https://developers.strava.com/)
- App created on the Strava developer panel (OAuth 2.0)

### 1️⃣ Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/strava-analytics.git
cd strava-analytics

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Credentials Setup

1. Copy the example file:
```bash
cp .env.example .env
```

2. Edit the `.env` file and fill in your credentials:
```env
STRAVA_ACCESS_TOKEN=your_access_token_here
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
STRAVA_REFRESH_TOKEN=your_refresh_token

EMAIL_RECIPIENT=your_email@gmail.com
EMAIL_SENDER=sender@gmail.com
EMAIL_APP_PASSWORD=gmail_app_password
```

⚠️ **IMPORTANT:** The `.env` file is in `.gitignore` and **must never be committed**. It contains sensitive information.

### 3️⃣ Getting Strava Credentials

#### Step-by-step guide:

1. Go to [Strava Developers](https://www.strava.com/settings/api)
2. Click **"Create New App"**
3. Fill in:
   - **Application Name:** Your project
   - **Category:** Data Analysis
   - **Website:** http://localhost
   - **Authorization Callback Domain:** `localhost`
4. After creating, copy the **Client ID** and **Client Secret**

#### Generate Access Token:

```bash
# 1. Open in browser (replace YOUR_CLIENT_ID):
https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all

# 2. Authorize and copy the 'code' from the return URL

# 3. Run in terminal (replace the values):
curl -X POST https://www.strava.com/oauth/token \
  -d client_id=YOUR_CLIENT_ID \
  -d client_secret=YOUR_CLIENT_SECRET \
  -d code=CODE_COPIED_FROM_URL \
  -d grant_type=authorization_code

# 4. Copy from the returned JSON:
#    - access_token
#    - refresh_token
```

### 4️⃣ Run the Data Extraction

```bash
# Run the ELT pipeline (first historical load)
python extract_load.py
```

This will:
- Create the `strava.db` database in the project folder
- Extract **all** your Strava activities (with automatic pagination)
- Load athlete profile, laps, and zones
- Generate log in `extract_load.log`

**⏱️ Estimated time:** 2-5 minutes depending on the number of activities

---

## 📊 Next Steps (Roadmap)

- [x] **Step 1:** ELT extraction and load pipeline
- [ ] **Step 2:** Transformation script with Pandas
- [ ] **Step 3:** Streamlit dashboard with interactive charts
- [ ] **Step 4:** GPS map visualization
- [ ] **Step 5:** PDF generation and email delivery
- [ ] **Step 6:** Biweekly automation (Schedule / Cron)
- [ ] **Step 7:** Server deployment (Streamlit Cloud / Railway)
- [ ] **Step 8:** Machine Learning for performance prediction

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Language** | Python 3.9+ |
| **API** | Strava API v3 (REST, OAuth 2.0) |
| **Database** | SQLite3 (local), PostgreSQL (future) |
| **Data Processing** | Pandas, NumPy |
| **Visualization** | Streamlit, Plotly, Folium |
| **PDF Generation** | ReportLab |
| **Automation** | Schedule (Python), Cron |
| **Machine Learning** | Scikit-learn, XGBoost *(future)* |
| **Deploy** | Streamlit Cloud, Railway, Docker *(future)* |

---

## 📂 File Structure

```
strava-analytics/
│
├── extract_load.py         # Main ELT pipeline
├── transform.py            # Transformations and feature engineering (next step)
├── dashboard.py            # Streamlit dashboard (next step)
├── generate_report.py      # PDF report generation (next step)
├── requirements.txt        # Project dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Files ignored by Git
├── README.md               # This file
│
├── strava.db               # SQLite database (auto-generated)
├── extract_load.log        # Execution log (auto-generated)
│
└── assets/                 # Images and resources (future)
    └── screenshots/
```

---

## 🔐 Security and Best Practices

✅ **What IS in the repository:**
- Python source code
- Complete documentation
- Configuration template (`.env.example`)
- Requirements and dependencies

❌ **What is NOT in the repository (protected by `.gitignore`):**
- `.env` file with credentials
- `strava.db` database with your personal data
- Generated PDF reports
- Execution logs

---

## 📈 Examples of Generated Analyses

### Monitored KPIs

- **Training Volume:** Total distance, total time, number of activities
- **Performance:** Average pace (min/km), average speed, time evolution
- **Physiological:** Average/max HR, time per HR zone, calories
- **Geospatial:** Route heat map, cumulative elevation, most frequent locations

### Calculated Metrics

- Pace by distance (5K, 10K, 21K, marathon)
- Aggregated weekly/monthly volume
- Performance progression over time
- Training consistency analysis
- Correlation between variables (e.g., HR x Pace)

---

## 🤝 Contributions

Contributions are welcome! Feel free to:

1. Fork the project
2. Create a branch for your feature (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

## 📝 License

This project is under the MIT license. See the [LICENSE](LICENSE) file for more details.

---

## 👤 Author

**Gabriel Biroli**

- LinkedIn: [linkedin.com/in/gabriel-biroli](https://www.linkedin.com/in/gabriel-biroli)
- Email: gabrielbiroli@gmail.com
- GitHub: [@g-biroli](https://github.com/g-biroli)

---

## 🙏 Acknowledgements

- [Strava API](https://developers.strava.com/) for the complete documentation
- The Python community for the excellence of open-source libraries
- All contributors and supporters of this project

---

## 📚 Useful Resources

- [Strava API Documentation](https://developers.strava.com/docs/reference/)
- [Strava API Playground](https://developers.strava.com/playground)
- [Strava OAuth 2.0 Guide](https://developers.strava.com/docs/authentication/)
- [Online Polyline Decoder](https://developers.google.com/maps/documentation/utilities/polylineutility)

---

<div align="center">

**⭐ If this project was useful, consider giving it a star on the repository!**

</div>
