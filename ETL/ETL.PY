"""ETL pipeline for MakFleet prototype

Usage:
  - Initialize DB:     python ETL/ETL.PY init-db
  - Seed drivers/vehicles: python ETL/ETL.PY seed
  - Generate sample telemetry and run pipeline: python ETL/ETL.PY generate --count 50
  - Load telemetry from CSV: python ETL/ETL.PY load-csv path/to/file.csv
  - Run full pipeline: python ETL/ETL.PY run

The script uses the project's SQLAlchemy models in `backend` and the SessionLocal
from `backend.database`. When run without a CSV it will generate synthetic
telemetry for existing vehicles.
"""
from __future__ import annotations

import os
import sys
import csv
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Iterable, List, Optional

# Ensure project root is on path so we can import backend package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import init_db, SessionLocal
from backend.models import Telemetry, Event, Vehicle


def parse_timestamp(ts: str) -> datetime:
	"""Parse several common timestamp formats into a datetime."""
	if isinstance(ts, datetime):
		return ts
	try:
		# ISO format
		return datetime.fromisoformat(ts)
	except Exception:
		formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]
		for fmt in formats:
			try:
				return datetime.strptime(ts, fmt)
			except Exception:
				continue
	# Fallback to now
	return datetime.utcnow()


def extract_from_csv(path: str) -> Iterable[Dict[str, Any]]:
	"""Yield telemetry rows from a CSV file.

	Expected headers: vehicle_id,latitude,longitude,speed,acceleration,engine_temp,fuel_level,timestamp
	"""
	with open(path, newline="") as fh:
		reader = csv.DictReader(fh)
		for row in reader:
			yield row


def generate_sample_telemetry(count: int = 50) -> List[Dict[str, Any]]:
	"""Generate synthetic telemetry data for vehicles present in DB."""
	db = SessionLocal()
	try:
		vehicles = db.query(Vehicle).all()
		if not vehicles:
			raise RuntimeError("No vehicles found in database. Run seed first.")

		data = []
		now = datetime.utcnow()
		for _ in range(count):
			v = random.choice(vehicles)
			ts = now - timedelta(seconds=random.randint(0, 3600))
			row = {
				"vehicle_id": v.vehicle_id,
				"latitude": round(0.33 + random.uniform(-0.005, 0.005), 6),
				"longitude": round(32.56 + random.uniform(-0.01, 0.01), 6),
				"speed": round(random.uniform(0, 100), 2),
				"acceleration": round(random.uniform(-6, 3), 2),
				"engine_temp": round(random.uniform(60, 110), 1),
				"fuel_level": round(random.uniform(10, 100), 1),
				"timestamp": ts.isoformat(),
			}
			data.append(row)

		return data
	finally:
		db.close()


def transform_row(row: Dict[str, Any]) -> Dict[str, Any]:
	"""Normalize and convert data types for insertion."""
	return {
		"vehicle_id": int(row["vehicle_id"]),
		"latitude": float(row["latitude"]),
		"longitude": float(row["longitude"]),
		"speed": float(row.get("speed") or 0.0),
		"acceleration": float(row.get("acceleration") or 0.0),
		"engine_temp": float(row.get("engine_temp") or 0.0),
		"fuel_level": float(row.get("fuel_level") or 0.0),
		"timestamp": parse_timestamp(row.get("timestamp") or row.get("time") or datetime.utcnow()),
	}


def load_telemetry(rows: Iterable[Dict[str, Any]]) -> int:
	"""Insert telemetry rows into the database. Returns number inserted."""
	db = SessionLocal()
	inserted = 0
	try:
		for raw in rows:
			r = transform_row(raw)
			t = Telemetry(
				vehicle_id=r["vehicle_id"],
				latitude=r["latitude"],
				longitude=r["longitude"],
				speed=r["speed"],
				acceleration=r.get("acceleration"),
				engine_temp=r.get("engine_temp"),
				fuel_level=r.get("fuel_level"),
				timestamp=r["timestamp"],
			)
			db.add(t)
			inserted += 1
		db.commit()
		print(f"Inserted {inserted} telemetry rows")
		return inserted
	except Exception as e:
		db.rollback()
		raise
	finally:
		db.close()


def detect_events_from_recent(limit: int = 1000) -> int:
	"""Scan recent telemetry and create Event rows based on simple rules.

	Rules implemented:
	  - Overspeed: speed > 80 -> event_type 'overspeed'
	  - Harsh braking: acceleration < -3 -> 'harsh_braking'
	  - High engine temp: engine_temp > 100 -> 'high_engine_temp'
	"""
	db = SessionLocal()
	created = 0
	try:
		recent = db.query(Telemetry).order_by(Telemetry.timestamp.desc()).limit(limit).all()
		for t in recent:
			ev_type: Optional[str] = None
			if t.speed and t.speed > 80:
				ev_type = "overspeed"
			if t.acceleration is not None and t.acceleration < -3:
				ev_type = "harsh_braking"
			if t.engine_temp and t.engine_temp > 100:
				ev_type = "high_engine_temp"

			if ev_type:
				e = Event(
					vehicle_id=t.vehicle_id,
					event_type=ev_type,
					latitude=t.latitude,
					longitude=t.longitude,
					speed=t.speed,
					acceleration=t.acceleration,
					timestamp=t.timestamp,
					severity="high" if ev_type in ("harsh_braking", "high_engine_temp") else "medium",
				)
				db.add(e)
				created += 1
		if created:
			db.commit()
		print(f"Created {created} events from recent telemetry")
		return created
	except Exception:
		db.rollback()
		raise
	finally:
		db.close()


def run_pipeline(sample_count: Optional[int] = None, csv_path: Optional[str] = None) -> None:
	"""Run full ETL pipeline: load telemetry (sample or CSV) then detect events."""
	if csv_path:
		rows = extract_from_csv(csv_path)
		load_telemetry(rows)
	else:
		if sample_count is None:
			sample_count = 100
		rows = generate_sample_telemetry(sample_count)
		load_telemetry(rows)

	detect_events_from_recent()


def main(argv: Optional[List[str]] = None) -> None:
	import argparse

	parser = argparse.ArgumentParser(description="MakFleet ETL utility")
	sub = parser.add_subparsers(dest="cmd")

	sub.add_parser("init-db", help="Create database tables")
	sub.add_parser("seed", help="Seed drivers and vehicles (calls seed_data.py)")

	gen = sub.add_parser("generate", help="Generate sample telemetry and run pipeline")
	gen.add_argument("--count", type=int, default=50)

	csvp = sub.add_parser("load-csv", help="Load telemetry from CSV and run pipeline")
	csvp.add_argument("path", help="Path to CSV file")

	sub.add_parser("run", help="Run full pipeline with generated sample telemetry")

	args = parser.parse_args(argv)

	if args.cmd == "init-db":
		init_db()
		return

	if args.cmd == "seed":
		# Use project's seed_data module
		from seed_data import seed_drivers_and_vehicles

		init_db()
		seed_drivers_and_vehicles()
		return

	if args.cmd == "generate":
		init_db()
		run_pipeline(sample_count=args.count)
		return

	if args.cmd == "load-csv":
		init_db()
		run_pipeline(csv_path=args.path)
		return

	if args.cmd == "run":
		init_db()
		run_pipeline()
		return

	parser.print_help()


if __name__ == "__main__":
	main()

