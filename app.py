from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from flask import Flask, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "suinogest.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "suinogest-secret-key"


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_: Any) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS pigs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT UNIQUE NOT NULL,
            breed TEXT NOT NULL,
            sex TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            weight_kg REAL NOT NULL,
            status TEXT NOT NULL,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS health_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pig_id INTEGER NOT NULL,
            event_date TEXT NOT NULL,
            event_type TEXT NOT NULL,
            description TEXT NOT NULL,
            cost REAL NOT NULL,
            FOREIGN KEY (pig_id) REFERENCES pigs (id)
        );

        CREATE TABLE IF NOT EXISTS feed_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT NOT NULL,
            feed_type TEXT NOT NULL,
            quantity_kg REAL NOT NULL,
            cost REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pig_id INTEGER,
            sale_date TEXT NOT NULL,
            buyer TEXT NOT NULL,
            value REAL NOT NULL,
            FOREIGN KEY (pig_id) REFERENCES pigs (id)
        );
        """
    )
    db.commit()
    db.close()


@app.route("/")
def dashboard() -> str:
    db = get_db()
    totals = {
        "pigs": db.execute("SELECT COUNT(*) as v FROM pigs").fetchone()["v"],
        "active": db.execute("SELECT COUNT(*) as v FROM pigs WHERE status='Ativo'").fetchone()["v"],
        "feed_cost": db.execute("SELECT COALESCE(SUM(cost),0) as v FROM feed_logs").fetchone()["v"],
        "health_cost": db.execute("SELECT COALESCE(SUM(cost),0) as v FROM health_events").fetchone()["v"],
        "revenue": db.execute("SELECT COALESCE(SUM(value),0) as v FROM sales").fetchone()["v"],
    }
    margin = totals["revenue"] - (totals["feed_cost"] + totals["health_cost"])
    recent_pigs = db.execute("SELECT * FROM pigs ORDER BY id DESC LIMIT 5").fetchall()
    return render_template("dashboard.html", totals=totals, margin=margin, recent_pigs=recent_pigs)


@app.route("/pigs")
def pigs_list() -> str:
    rows = get_db().execute("SELECT * FROM pigs ORDER BY id DESC").fetchall()
    return render_template("pigs.html", pigs=rows)


@app.route("/pigs/new", methods=["GET", "POST"])
def pigs_new() -> str:
    if request.method == "POST":
        data = (
            request.form["tag"].strip(),
            request.form["breed"].strip(),
            request.form["sex"],
            request.form["birth_date"],
            float(request.form["weight_kg"]),
            request.form["status"],
            request.form.get("notes", "").strip(),
        )
        db = get_db()
        try:
            db.execute(
                """
                INSERT INTO pigs (tag, breed, sex, birth_date, weight_kg, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                data,
            )
            db.commit()
            flash("Suíno cadastrado com sucesso.", "success")
            return redirect(url_for("pigs_list"))
        except sqlite3.IntegrityError:
            flash("Brinco já cadastrado. Use um identificador único.", "danger")
    return render_template("pig_form.html", today=date.today().isoformat())


@app.route("/health", methods=["GET", "POST"])
def health() -> str:
    db = get_db()
    pigs = db.execute("SELECT id, tag FROM pigs ORDER BY tag").fetchall()
    if request.method == "POST":
        db.execute(
            """
            INSERT INTO health_events (pig_id, event_date, event_type, description, cost)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(request.form["pig_id"]),
                request.form["event_date"],
                request.form["event_type"],
                request.form["description"],
                float(request.form["cost"]),
            ),
        )
        db.commit()
        flash("Evento sanitário registrado.", "success")
        return redirect(url_for("health"))

    events = db.execute(
        """
        SELECT h.*, p.tag FROM health_events h
        JOIN pigs p ON p.id = h.pig_id
        ORDER BY h.event_date DESC, h.id DESC
        """
    ).fetchall()
    return render_template("health.html", pigs=pigs, events=events, today=date.today().isoformat())


@app.route("/feed", methods=["GET", "POST"])
def feed() -> str:
    db = get_db()
    if request.method == "POST":
        db.execute(
            "INSERT INTO feed_logs (log_date, feed_type, quantity_kg, cost) VALUES (?, ?, ?, ?)",
            (
                request.form["log_date"],
                request.form["feed_type"],
                float(request.form["quantity_kg"]),
                float(request.form["cost"]),
            ),
        )
        db.commit()
        flash("Consumo de ração registrado.", "success")
        return redirect(url_for("feed"))

    logs = db.execute("SELECT * FROM feed_logs ORDER BY log_date DESC, id DESC").fetchall()
    return render_template("feed.html", logs=logs, today=date.today().isoformat())


@app.route("/sales", methods=["GET", "POST"])
def sales() -> str:
    db = get_db()
    pigs = db.execute("SELECT id, tag FROM pigs ORDER BY tag").fetchall()
    if request.method == "POST":
        pig_id_raw = request.form.get("pig_id", "")
        pig_id = int(pig_id_raw) if pig_id_raw else None
        db.execute(
            "INSERT INTO sales (pig_id, sale_date, buyer, value) VALUES (?, ?, ?, ?)",
            (pig_id, request.form["sale_date"], request.form["buyer"], float(request.form["value"])),
        )
        if pig_id:
            db.execute("UPDATE pigs SET status='Vendido' WHERE id=?", (pig_id,))
        db.commit()
        flash("Venda registrada.", "success")
        return redirect(url_for("sales"))

    rows = db.execute(
        """
        SELECT s.*, p.tag FROM sales s
        LEFT JOIN pigs p ON p.id = s.pig_id
        ORDER BY s.sale_date DESC, s.id DESC
        """
    ).fetchall()
    return render_template("sales.html", sales=rows, pigs=pigs, today=date.today().isoformat())


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
