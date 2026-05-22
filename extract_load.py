"""
=============================================================================
ETAPA 1 — Extract & Load | Pipeline ELT Strava
=============================================================================
Tabelas:
  · athlete          — perfil do atleta (1 linha, atualizada a cada carga)
  · activities       — todas as atividades paginadas
  · activity_laps    — voltas/splits de cada atividade
  · activity_zones   — tempo em cada zona de FC/potência
  · activity_streams — série temporal completa (GPS, FC, pace, altitude...)
=============================================================================
Credenciais carregadas do arquivo .env (nunca commitar o .env!)
=============================================================================
"""

import os
import json
import time
import logging
import sqlite3
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# ⚙️  CARREGAMENTO DE CREDENCIAIS — via .env
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

ACCESS_TOKEN  = os.getenv("STRAVA_ACCESS_TOKEN", "")
CLIENT_ID     = os.getenv("STRAVA_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET", "")
REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN", "")

if not all([ACCESS_TOKEN, CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
    raise EnvironmentError(
        "Credenciais Strava não encontradas. "
        "Copie .env.example para .env e preencha os valores."
    )

# ---------------------------------------------------------------------------
# ⚙️  CONFIGURAÇÕES GERAIS
# ---------------------------------------------------------------------------

DB_PATH          = BASE_DIR / "data" / "strava.db"
BASE_URL         = "https://www.strava.com/api/v3"
PER_PAGE         = 200
RATE_LIMIT_PAUSE = 1.2
STREAM_KEYS      = "time,distance,latlng,altitude,heartrate,cadence,velocity_smooth,moving,grade_smooth,watts,temp"

# ---------------------------------------------------------------------------
# 🪵  LOGGING
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(BASE_DIR / "data" / "extract_load.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 🗄️  SCHEMAS DAS TABELAS
# ---------------------------------------------------------------------------

SCHEMA_ATHLETE = """
CREATE TABLE IF NOT EXISTS athlete (
    id                      INTEGER PRIMARY KEY,
    username                TEXT,
    firstname               TEXT,
    lastname                TEXT,
    city                    TEXT,
    state                   TEXT,
    country                 TEXT,
    sex                     TEXT,
    weight                  REAL,
    profile_medium          TEXT,
    profile                 TEXT,
    follower_count          INTEGER,
    friend_count            INTEGER,
    measurement_preference  TEXT,
    ftp                     INTEGER,
    updated_at              TEXT
);
"""

SCHEMA_ACTIVITIES = """
CREATE TABLE IF NOT EXISTS activities (
    id                      INTEGER PRIMARY KEY,
    athlete_id              INTEGER,
    name                    TEXT,
    start_date              TEXT,
    start_date_local        TEXT,
    timezone                TEXT,
    type                    TEXT,
    sport_type              TEXT,
    workout_type            INTEGER,
    distance                REAL,
    moving_time             INTEGER,
    elapsed_time            INTEGER,
    average_speed           REAL,
    max_speed               REAL,
    total_elevation_gain    REAL,
    elev_high               REAL,
    elev_low                REAL,
    average_heartrate       REAL,
    max_heartrate           REAL,
    has_heartrate           INTEGER,
    average_cadence         REAL,
    average_watts           REAL,
    max_watts               INTEGER,
    weighted_average_watts  INTEGER,
    kilojoules              REAL,
    device_watts            INTEGER,
    average_temp            INTEGER,
    start_latlng            TEXT,
    end_latlng              TEXT,
    map_id                  TEXT,
    map_summary_polyline    TEXT,
    location_city           TEXT,
    location_state          TEXT,
    location_country        TEXT,
    achievement_count       INTEGER,
    kudos_count             INTEGER,
    pr_count                INTEGER,
    athlete_count           INTEGER,
    gear_id                 TEXT,
    device_name             TEXT,
    visibility              TEXT,
    manual                  INTEGER,
    private                 INTEGER,
    flagged                 INTEGER,
    trainer                 INTEGER,
    commute                 INTEGER,
    description             TEXT,
    calories                REAL,
    raw_json                TEXT,
    loaded_at               TEXT,
    FOREIGN KEY (athlete_id) REFERENCES athlete(id)
);
"""

SCHEMA_LAPS = """
CREATE TABLE IF NOT EXISTS activity_laps (
    id                      INTEGER PRIMARY KEY,
    activity_id             INTEGER NOT NULL,
    lap_index               INTEGER,
    name                    TEXT,
    elapsed_time            INTEGER,
    moving_time             INTEGER,
    distance                REAL,
    start_date_local        TEXT,
    average_speed           REAL,
    max_speed               REAL,
    average_heartrate       REAL,
    max_heartrate           REAL,
    average_cadence         REAL,
    average_watts           REAL,
    total_elevation_gain    REAL,
    pace_zone               INTEGER,
    split                   INTEGER,
    loaded_at               TEXT,
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);
"""

SCHEMA_ZONES = """
CREATE TABLE IF NOT EXISTS activity_zones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id     INTEGER NOT NULL,
    zone_type       TEXT,
    zone_index      INTEGER,
    zone_min        INTEGER,
    zone_max        INTEGER,
    time_in_zone    INTEGER,
    loaded_at       TEXT,
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);
"""

SCHEMA_STREAMS = """
CREATE TABLE IF NOT EXISTS activity_streams (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id     INTEGER NOT NULL,
    time_seconds    INTEGER,
    lat             REAL,
    lng             REAL,
    altitude        REAL,
    grade_smooth    REAL,
    distance        REAL,
    velocity_smooth REAL,
    moving          INTEGER,
    heartrate       INTEGER,
    cadence         INTEGER,
    watts           INTEGER,
    temp            INTEGER,
    loaded_at       TEXT,
    FOREIGN KEY (activity_id) REFERENCES activities(id)
);
CREATE INDEX IF NOT EXISTS idx_streams_activity ON activity_streams(activity_id);
"""

# ---------------------------------------------------------------------------
# 🧱  BANCO DE DADOS
# ---------------------------------------------------------------------------

def create_database() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    for schema in [SCHEMA_ATHLETE, SCHEMA_ACTIVITIES, SCHEMA_LAPS, SCHEMA_ZONES, SCHEMA_STREAMS]:
        conn.executescript(schema)
    conn.commit()
    log.info(f"Banco de dados pronto em: {DB_PATH}")
    return conn

# ---------------------------------------------------------------------------
# 🔐  AUTENTICAÇÃO
# ---------------------------------------------------------------------------

def get_headers() -> dict:
    return {"Authorization": f"Bearer {ACCESS_TOKEN}"}


def refresh_access_token():
    global ACCESS_TOKEN
    r = requests.post("https://www.strava.com/oauth/token", data={
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type":    "refresh_token",
    })
    r.raise_for_status()
    ACCESS_TOKEN = r.json()["access_token"]
    log.info("Access Token renovado com sucesso.")

# ---------------------------------------------------------------------------
# 📥  EXTRAÇÃO — ATLETA
# ---------------------------------------------------------------------------

def fetch_athlete(conn: sqlite3.Connection):
    r = requests.get(f"{BASE_URL}/athlete", headers=get_headers())
    r.raise_for_status()
    a = r.json()
    conn.execute("""
        INSERT INTO athlete
            (id, username, firstname, lastname, city, state, country, sex,
             weight, profile_medium, profile, follower_count, friend_count,
             measurement_preference, ftp, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
            weight=excluded.weight,
            follower_count=excluded.follower_count,
            friend_count=excluded.friend_count,
            ftp=excluded.ftp,
            updated_at=excluded.updated_at;
    """, (
        a.get("id"), a.get("username"), a.get("firstname"), a.get("lastname"),
        a.get("city"), a.get("state"), a.get("country"), a.get("sex"),
        a.get("weight"), a.get("profile_medium"), a.get("profile"),
        a.get("follower_count"), a.get("friend_count"),
        a.get("measurement_preference"), a.get("ftp"),
        datetime.utcnow().isoformat(),
    ))
    conn.commit()
    log.info(f"Atleta carregado: {a.get('firstname')} {a.get('lastname')}")

# ---------------------------------------------------------------------------
# 📥  EXTRAÇÃO — ATIVIDADES
# ---------------------------------------------------------------------------

def parse_activity(raw: dict) -> dict:
    map_obj  = raw.get("map") or {}
    start_ll = raw.get("start_latlng")
    end_ll   = raw.get("end_latlng")
    return {
        "id":                     raw.get("id"),
        "athlete_id":             (raw.get("athlete") or {}).get("id"),
        "name":                   raw.get("name"),
        "start_date":             raw.get("start_date"),
        "start_date_local":       raw.get("start_date_local"),
        "timezone":               raw.get("timezone"),
        "type":                   raw.get("type"),
        "sport_type":             raw.get("sport_type"),
        "workout_type":           raw.get("workout_type"),
        "distance":               raw.get("distance"),
        "moving_time":            raw.get("moving_time"),
        "elapsed_time":           raw.get("elapsed_time"),
        "average_speed":          raw.get("average_speed"),
        "max_speed":              raw.get("max_speed"),
        "total_elevation_gain":   raw.get("total_elevation_gain"),
        "elev_high":              raw.get("elev_high"),
        "elev_low":               raw.get("elev_low"),
        "average_heartrate":      raw.get("average_heartrate"),
        "max_heartrate":          raw.get("max_heartrate"),
        "has_heartrate":          int(raw.get("has_heartrate", False)),
        "average_cadence":        raw.get("average_cadence"),
        "average_watts":          raw.get("average_watts"),
        "max_watts":              raw.get("max_watts"),
        "weighted_average_watts": raw.get("weighted_average_watts"),
        "kilojoules":             raw.get("kilojoules"),
        "device_watts":           int(raw.get("device_watts", False)),
        "average_temp":           raw.get("average_temp"),
        "start_latlng":           json.dumps(start_ll) if start_ll else None,
        "end_latlng":             json.dumps(end_ll)   if end_ll   else None,
        "map_id":                 map_obj.get("id"),
        "map_summary_polyline":   map_obj.get("summary_polyline"),
        "location_city":          raw.get("location_city"),
        "location_state":         raw.get("location_state"),
        "location_country":       raw.get("location_country"),
        "achievement_count":      raw.get("achievement_count"),
        "kudos_count":            raw.get("kudos_count"),
        "pr_count":               raw.get("pr_count"),
        "athlete_count":          raw.get("athlete_count"),
        "gear_id":                raw.get("gear_id"),
        "device_name":            raw.get("device_name"),
        "visibility":             raw.get("visibility"),
        "manual":                 int(raw.get("manual", False)),
        "private":                int(raw.get("private", False)),
        "flagged":                int(raw.get("flagged", False)),
        "trainer":                int(raw.get("trainer", False)),
        "commute":                int(raw.get("commute", False)),
        "description":            raw.get("description"),
        "calories":               raw.get("calories"),
        "raw_json":               json.dumps(raw),
        "loaded_at":              datetime.utcnow().isoformat(),
    }


INSERT_ACTIVITY = """
INSERT OR IGNORE INTO activities (
    id, athlete_id, name, start_date, start_date_local, timezone,
    type, sport_type, workout_type, distance, moving_time, elapsed_time,
    average_speed, max_speed, total_elevation_gain, elev_high, elev_low,
    average_heartrate, max_heartrate, has_heartrate,
    average_cadence, average_watts, max_watts, weighted_average_watts,
    kilojoules, device_watts, average_temp,
    start_latlng, end_latlng, map_id, map_summary_polyline,
    location_city, location_state, location_country,
    achievement_count, kudos_count, pr_count, athlete_count,
    gear_id, device_name, visibility, manual, private, flagged,
    trainer, commute, description, calories, raw_json, loaded_at
) VALUES (
    :id, :athlete_id, :name, :start_date, :start_date_local, :timezone,
    :type, :sport_type, :workout_type, :distance, :moving_time, :elapsed_time,
    :average_speed, :max_speed, :total_elevation_gain, :elev_high, :elev_low,
    :average_heartrate, :max_heartrate, :has_heartrate,
    :average_cadence, :average_watts, :max_watts, :weighted_average_watts,
    :kilojoules, :device_watts, :average_temp,
    :start_latlng, :end_latlng, :map_id, :map_summary_polyline,
    :location_city, :location_state, :location_country,
    :achievement_count, :kudos_count, :pr_count, :athlete_count,
    :gear_id, :device_name, :visibility, :manual, :private, :flagged,
    :trainer, :commute, :description, :calories, :raw_json, :loaded_at
);
"""

# ---------------------------------------------------------------------------
# 📥  EXTRAÇÃO — LAPS
# ---------------------------------------------------------------------------

def fetch_laps(activity_id: int, conn: sqlite3.Connection):
    r = requests.get(f"{BASE_URL}/activities/{activity_id}/laps", headers=get_headers())
    if r.status_code != 200:
        return
    now  = datetime.utcnow().isoformat()
    rows = [(
        lap.get("id"), activity_id, lap.get("lap_index"), lap.get("name"),
        lap.get("elapsed_time"), lap.get("moving_time"), lap.get("distance"),
        lap.get("start_date_local"), lap.get("average_speed"), lap.get("max_speed"),
        lap.get("average_heartrate"), lap.get("max_heartrate"),
        lap.get("average_cadence"), lap.get("average_watts"),
        lap.get("total_elevation_gain"), lap.get("pace_zone"), lap.get("split"), now,
    ) for lap in r.json()]
    conn.executemany("""
        INSERT OR IGNORE INTO activity_laps
            (id, activity_id, lap_index, name, elapsed_time, moving_time, distance,
             start_date_local, average_speed, max_speed, average_heartrate, max_heartrate,
             average_cadence, average_watts, total_elevation_gain, pace_zone, split, loaded_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)
    conn.commit()

# ---------------------------------------------------------------------------
# 📥  EXTRAÇÃO — ZONES
# ---------------------------------------------------------------------------

def fetch_zones(activity_id: int, conn: sqlite3.Connection):
    r = requests.get(f"{BASE_URL}/activities/{activity_id}/zones", headers=get_headers())
    if r.status_code != 200:
        return
    now  = datetime.utcnow().isoformat()
    rows = []
    for zone_group in r.json():
        zone_type = zone_group.get("type")
        for i, bucket in enumerate(zone_group.get("distribution_buckets", [])):
            rows.append((activity_id, zone_type, i + 1,
                         bucket.get("min"), bucket.get("max"), bucket.get("time"), now))
    if rows:
        conn.executemany("""
            INSERT INTO activity_zones
                (activity_id, zone_type, zone_index, zone_min, zone_max, time_in_zone, loaded_at)
            VALUES (?,?,?,?,?,?,?)
        """, rows)
        conn.commit()

# ---------------------------------------------------------------------------
# 📥  EXTRAÇÃO — STREAMS (GPS ponto a ponto)
# ---------------------------------------------------------------------------

def fetch_streams(activity_id: int, conn: sqlite3.Connection):
    exists = conn.execute(
        "SELECT 1 FROM activity_streams WHERE activity_id=? LIMIT 1", (activity_id,)
    ).fetchone()
    if exists:
        return

    r = requests.get(
        f"{BASE_URL}/activities/{activity_id}/streams",
        headers=get_headers(),
        params={"keys": STREAM_KEYS, "key_by_type": "true"},
    )
    if r.status_code != 200:
        return

    data       = r.json()
    now        = datetime.utcnow().isoformat()
    time_data  = (data.get("time")            or {}).get("data", [])
    dist_data  = (data.get("distance")        or {}).get("data", [])
    ll_data    = (data.get("latlng")          or {}).get("data", [])
    alt_data   = (data.get("altitude")        or {}).get("data", [])
    hr_data    = (data.get("heartrate")       or {}).get("data", [])
    cad_data   = (data.get("cadence")         or {}).get("data", [])
    vel_data   = (data.get("velocity_smooth") or {}).get("data", [])
    mov_data   = (data.get("moving")          or {}).get("data", [])
    grade_data = (data.get("grade_smooth")    or {}).get("data", [])
    watt_data  = (data.get("watts")           or {}).get("data", [])
    temp_data  = (data.get("temp")            or {}).get("data", [])

    def s(lst, i):
        try: return lst[i]
        except: return None

    rows = []
    for i, t in enumerate(time_data):
        ll = s(ll_data, i) or [None, None]
        rows.append((
            activity_id, t, ll[0], ll[1],
            s(alt_data, i), s(grade_data, i), s(dist_data, i),
            s(vel_data, i), int(s(mov_data, i) or 0),
            s(hr_data, i), s(cad_data, i), s(watt_data, i), s(temp_data, i), now,
        ))

    conn.executemany("""
        INSERT INTO activity_streams
            (activity_id, time_seconds, lat, lng, altitude, grade_smooth,
             distance, velocity_smooth, moving, heartrate, cadence, watts, temp, loaded_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)
    conn.commit()

# ---------------------------------------------------------------------------
# 🎯  ORQUESTRADOR PRINCIPAL
# ---------------------------------------------------------------------------

def extract_all_activities(conn: sqlite3.Connection, load_streams: bool = False) -> int:
    """
    load_streams=False  → carga histórica rápida (recomendado na primeira vez)
    load_streams=True   → enriquece com GPS detalhado (use incrementalmente)
    """
    url       = f"{BASE_URL}/athlete/activities"
    page      = 1
    total_new = 0
    total_old = 0

    log.info("=" * 60)
    log.info(f"Extração iniciada | streams={load_streams}")
    log.info("=" * 60)

    while True:
        r = requests.get(url, headers=get_headers(), params={"per_page": PER_PAGE, "page": page})

        if r.status_code == 401:
            log.warning("Token expirado — renovando...")
            refresh_access_token()
            continue
        if r.status_code == 429:
            log.warning("Rate limit — aguardando 60s...")
            time.sleep(60)
            continue
        if r.status_code != 200:
            log.error(f"HTTP {r.status_code}: {r.text}")
            break

        batch = r.json()
        if not batch:
            log.info(f"Paginação concluída na página {page}.")
            break

        page_new = 0
        for raw in batch:
            result = conn.execute(INSERT_ACTIVITY, parse_activity(raw))
            if result.rowcount > 0:
                aid = raw["id"]
                page_new += 1
                total_new += 1
                fetch_laps(aid, conn)
                fetch_zones(aid, conn)
                time.sleep(0.3)
                if load_streams:
                    fetch_streams(aid, conn)
                    time.sleep(0.5)
            else:
                total_old += 1

        conn.commit()
        log.info(f"Pág {page:>3}: {len(batch):>3} recebidas | {page_new:>3} novas | {len(batch)-page_new:>3} skip")
        page += 1
        time.sleep(RATE_LIMIT_PAUSE)

    log.info(f"\n{'='*60}")
    log.info(f"  ✅ Atividades novas : {total_new}")
    log.info(f"  ⭐  Já existiam      : {total_old}")
    log.info(f"{'='*60}")
    return total_new

# ---------------------------------------------------------------------------
# ▶️  EXECUÇÃO
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    log.info(f"Diretório do projeto : {BASE_DIR}")
    log.info(f"Banco de dados       : {DB_PATH}")

    conn = create_database()
    fetch_athlete(conn)
    extract_all_activities(conn, load_streams=False)
    conn.close()
    log.info("Pipeline finalizado.")
