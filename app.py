"""My Festival REST API — M10 (Flask + SQLite)."""

import os
import re
import sqlite3
from datetime import date, datetime, timedelta

from flask import Flask, jsonify, request

app = Flask(__name__)

# Asetuksen voi tarvittaessa muuttaa DB_PATH-ymparistomuuttujalla.
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "myfestival.db"))


def get_db():
    """Avaa SQLite-yhteys ja ottaa viiteavaintarkistukset kayttoon."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # Rivit voidaan muuttaa JSON-sanakirjoiksi.
    return conn


@app.get("/")
def health():
    """Palauttaa merkin siita, etta API on kaynnissa."""
    return jsonify(status="ok", endpoints=[
        "/api/artists", "/api/days", "/api/stages",
        "/api/artists/<id>/events", "/api/timetable?day=YYYY-MM-DD",
        "POST /api/events", "DELETE /api/events/<id>",
    ])


@app.get("/api/artists")
def get_artists():
    """Palauttaa kaikki artistit aakkosjarjestyksessa (200)."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT artist_id, name, country FROM Artist ORDER BY name"
        ).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@app.get("/api/days")
def get_days():
    """Palauttaa paivat ja niiden tunnisteet (200)."""
    conn = get_db()
    try:
        rows = conn.execute("SELECT day_id, date FROM Day ORDER BY date").fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@app.get("/api/stages")
def get_stages():
    """Palauttaa lavat ja niiden tunnisteet (200)."""
    conn = get_db()
    try:
        rows = conn.execute("SELECT stage_id, name FROM Stage ORDER BY stage_id").fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@app.get("/api/artists/<int:artist_id>/events")
def get_artist_events(artist_id):
    """Hakee yhden artistin esiintymiset. Tuntematon artisti -> 404."""
    conn = get_db()
    try:
        
        artist = conn.execute(
            "SELECT artist_id FROM Artist WHERE artist_id = ?", (artist_id,)
        ).fetchone()
        if artist is None:
            return jsonify(error="Artistia ei loytynyt"), 404

        rows = conn.execute(
            """SELECT e.event_id, d.date AS day, s.name AS stage,
                      time(e.start_dt) AS starts
               FROM Event AS e
               JOIN Day AS d ON e.day_id = d.day_id
               JOIN Stage AS s ON e.stage_id = s.stage_id
               JOIN EventType AS et ON e.event_type_id = et.event_type_id
               WHERE e.artist_id = ? AND et.code = 'performance'
               ORDER BY d.date, e.start_dt, s.name""",
            (artist_id,),
        ).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@app.get("/api/timetable")
def get_timetable():
    """Hakee koko aikataulun tai yhden paivan tapahtumat."""
    day = request.args.get("day")

    if day is not None:
        # Vaaditaan oikea kalenteripaivamaara muodossa VVVV-KK-PP.
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            return jsonify(error="Paivamaaran muodon pita olla YYYY-MM-DD"), 400
        try:
            date.fromisoformat(day)
        except ValueError:
            return jsonify(error="Virheellinen paivamaara"), 400

    sql = "SELECT date, stage, artist, starts, ends FROM V_Timetable"
    params = ()
    if day is not None:
        sql += " WHERE date = ?" 
        params = (day,)
    sql += " ORDER BY date, starts, stage"

    conn = get_db()
    try:
        rows = conn.execute(sql, params).fetchall()
        return jsonify([dict(row) for row in rows])
    finally:
        conn.close()


@app.post("/api/events")
def create_event():
    """Luo uuden 45 minuutin esiintymisen ja palauttaa sen id:n (201)."""
    body = request.get_json(silent=True)
    required = ("artist_id", "stage_id", "day_id", "start_dt")

    if not isinstance(body, dict) or any(body.get(field) is None for field in required):
        return jsonify(error="Pakolliset kentat: artist_id, stage_id, day_id, start_dt"), 400

   
    for field in ("artist_id", "stage_id", "day_id"):
        value = body[field]
        if type(value) is not int or value < 1:
            return jsonify(error=f"Kentassa {field} pitaa olla positiivinen kokonaisluku"), 400

    start_text = body["start_dt"]
    if not isinstance(start_text, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", start_text
    ):
        return jsonify(error="start_dt: odotettu muoto YYYY-MM-DD HH:MM:SS"), 400
    try:
        start = datetime.strptime(start_text, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return jsonify(error="start_dt ei ole kelvollinen ajankohta"), 400

    duration = 45
    end = start + timedelta(minutes=duration)
    end_text = end.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    try:
       
        day_row = conn.execute("SELECT date FROM Day WHERE day_id = ?", (body["day_id"],)).fetchone()
        if day_row is None or day_row["date"] != start.date().isoformat():
            return jsonify(error="day_id ei vastaa start_dt-paivamaaraa"), 400

        
        event_type = conn.execute(
            "SELECT event_type_id FROM EventType WHERE code = ?", ("performance",)
        ).fetchone()
        if event_type is None:
            return jsonify(error="Esiintymisen tyyppia ei loydy tietokannasta"), 500

        try:
            cursor = conn.execute(
                """INSERT INTO Event
                   (event_type_id, day_id, stage_id, artist_id, start_dt, end_dt, duration_min)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (event_type["event_type_id"], body["day_id"], body["stage_id"],
                 body["artist_id"], start_text, end_text, duration),
            )
            conn.commit() 
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            return jsonify(error=f"Tapahtuman lisays epaonnistui: {exc}"), 400

        return jsonify(
            event_id=cursor.lastrowid,
            artist_id=body["artist_id"],
            stage_id=body["stage_id"],
            day_id=body["day_id"],
            start_dt=start_text,
            end_dt=end_text,
            duration_min=duration,
        ), 201
    finally:
        conn.close()


@app.delete("/api/events/<int:event_id>")
def delete_event(event_id):
    """Poistaa tapahtuman. Onnistuu -> 204, tuntematon -> 404."""
    conn = get_db()
    try:
        cursor = conn.execute("DELETE FROM Event WHERE event_id = ?", (event_id,))
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify(error="Tapahtumaa ei loytynyt"), 404
        conn.commit()
        return "", 204
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
