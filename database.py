import csv
import sqlite3
from pathlib import Path
from datetime import datetime, timezone



# Store the database in the main project folder.

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "oceanguard.db"


def set_database_path(path):
    """Set the SQLite database file path."""
    global DB_PATH
    DB_PATH = Path(path)



def get_connection():
    """Connect to the OceanGuardAI SQLite database."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection



def initialize_database():
    """Create the observations table and upgrade it if needed."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_name TEXT NOT NULL,
                debris_type TEXT,
                confidence REAL,
                quantity INTEGER DEFAULT 1,
                latitude REAL,
                longitude REAL,
                detected_at TEXT NOT NULL,
                review_status TEXT NOT NULL DEFAULT 'Pending',
                notes TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Check whether the existing database has the updated_at column.
        columns = connection.execute(
            "PRAGMA table_info(observations)"
        ).fetchall()

        column_names = [column["name"] for column in columns]

        # Add the column to older databases without deleting existing records.
        if "updated_at" not in column_names:
            connection.execute("""
                ALTER TABLE observations
                ADD COLUMN updated_at TEXT
            """)

        # Set an initial timestamp for older records.
        connection.execute("""
            UPDATE observations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE updated_at IS NULL
        """)





def save_observation(
    image_name,
    debris_type=None,
    confidence=None,
    quantity=1,
    latitude=None,
    longitude=None,
    notes=None
):
    """Save one marine debris detection record."""


    if not image_name or not image_name.strip():
        raise ValueError("Image name cannot be empty.")

    
    if debris_type is not None and not debris_type.strip():
        raise ValueError("Debris type cannot be blank.")


    if confidence is not None and not 0 <= confidence <= 1:
        raise ValueError("Confidence must be between 0 and 1.")

    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")

    if (latitude is None) != (longitude is None):
        raise ValueError("Provide both latitude and longitude, or neither.")

    if latitude is not None:
        if not -90 <= latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90.")

        if not -180 <= longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180.")


    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO observations (
                image_name,
                debris_type,
                confidence,
                quantity,
                latitude,
                longitude,
                detected_at,
                review_status,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            image_name,
            debris_type,
            confidence,
            quantity,
            latitude,
            longitude,
            datetime.now(timezone.utc).isoformat(),
            "Pending",
            notes
        ))

        return cursor.lastrowid





def get_observations():
    """Return all saved observations, most recently updated first."""
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT *
            FROM observations
            ORDER BY updated_at DESC, id DESC
        """).fetchall()

    return [dict(row) for row in rows]



def get_observations_by_status(status):
    """Return observations matching a review status."""
    allowed_statuses = {"Pending", "Reviewed", "Rejected"}

    if status not in allowed_statuses:
        raise ValueError(
            "Status must be Pending, Reviewed, or Rejected."
        )

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT *
            FROM observations
            WHERE review_status = ?
            ORDER BY id DESC
        """, (status,)).fetchall()

    return [dict(row) for row in rows]



def check_database_integrity():
    """Check whether the SQLite database passes its integrity check."""
    with get_connection() as connection:
        result = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()

    return result[0] == "ok"


def get_observation_counts():
    """Return the number of observations for each review status."""
    counts = {
        "Pending": 0,
        "Reviewed": 0,
        "Rejected": 0
    }

    with get_connection() as connection:
        rows = connection.execute("""
            SELECT review_status, COUNT(*) AS total
            FROM observations
            GROUP BY review_status
        """).fetchall()

    for row in rows:
        if row["review_status"] in counts:
            counts[row["review_status"]] = row["total"]

    return counts


def get_debris_type_counts():
    """Count observations grouped by debris type."""
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT
                COALESCE(debris_type, 'Unknown') AS debris_type,
                COUNT(*) AS total
            FROM observations
            GROUP BY COALESCE(debris_type, 'Unknown')
            ORDER BY total DESC
        """).fetchall()

    return {
        row["debris_type"]: row["total"]
        for row in rows
    }


def get_average_confidence():
    """Calculate the average confidence of saved detections."""
    with get_connection() as connection:
        row = connection.execute("""
            SELECT AVG(confidence) AS average_confidence
            FROM observations
            WHERE confidence IS NOT NULL
        """).fetchone()

    return row["average_confidence"]


def get_total_observations():
    """Return the total number of saved observations."""
    with get_connection() as connection:
        row = connection.execute("""
            SELECT COUNT(*) AS total
            FROM observations
        """).fetchone()

    return row["total"]


def get_analytics_summary():
    """Return a summary of the saved observations."""
    average_confidence = get_average_confidence()

    return {
        "total_observations": get_total_observations(),
        "debris_type_counts": get_debris_type_counts(),
        "average_confidence": (
            round(average_confidence, 2)
            if average_confidence is not None
            else None
        )
    }



def update_review_status(record_id, status, notes=None):
    """Update the review status, notes, and last-updated time."""
    allowed_statuses = {"Pending", "Reviewed", "Rejected"}

    if status not in allowed_statuses:
        raise ValueError(
            "Status must be Pending, Reviewed, or Rejected."
        )

    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE observations
            SET review_status = ?,
                notes = COALESCE(?, notes),
                updated_at = datetime('now', 'localtime')
            WHERE id = ?
        """, (status, notes, record_id))

        return cursor.rowcount > 0


def update_observation_gps(record_id, latitude, longitude):
    """Update GPS coordinates for an existing observation."""

    if latitude is None or longitude is None:
        raise ValueError("Both latitude and longitude are required.")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    with get_connection() as connection:
        cursor = connection.execute("""
            UPDATE observations
            SET latitude = ?,
                longitude = ?,
                updated_at = datetime('now', 'localtime')
            WHERE id = ?
        """, (latitude, longitude, record_id))

        return cursor.rowcount > 0

def export_observations_to_csv(output_path=None):
    """Export all observations to a CSV file."""
    if output_path is None:
        output_path = BASE_DIR / "observations_export.csv"

    records = get_observations()

    fieldnames = [
        "id",
        "image_name",
        "debris_type",
        "confidence",
        "quantity",
        "latitude",
        "longitude",
        "detected_at",
        "review_status",
        "notes",
        "updated_at"
    ]

    with open(output_path, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return output_path


if __name__ == "__main__":
    initialize_database()
    print("OceanGuardAI database initialized successfully!")
    print(f"Database location: {DB_PATH}")




def test_database_integrity():
    assert check_database_integrity() is True