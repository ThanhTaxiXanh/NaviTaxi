-- NaviTaxi Road Intelligence v1; empty schema: never fabricate real speeds or sign positions.
PRAGMA foreign_keys = ON;
PRAGMA user_version = 1;

CREATE TABLE IF NOT EXISTS data_sources (
    source_id TEXT PRIMARY KEY CHECK (length(source_id) > 0),
    provider TEXT NOT NULL CHECK (length(provider) > 0),
    source_uri TEXT NOT NULL CHECK (length(source_uri) > 0),
    license TEXT NOT NULL CHECK (length(license) > 0),
    acquired_at TEXT NOT NULL,
    checksum_sha256 TEXT NOT NULL CHECK (length(checksum_sha256) = 64),
    dataset_version TEXT
);

CREATE TABLE IF NOT EXISTS road_segments (
    segment_pk INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id TEXT NOT NULL UNIQUE,
    osm_way_id INTEGER,
    direction TEXT NOT NULL CHECK (direction IN ('forward','backward','both')),
    vehicle_class TEXT NOT NULL DEFAULT 'motorcar',
    speed_kmh INTEGER NOT NULL CHECK (speed_kmh BETWEEN 1 AND 250),
    geometry_geojson TEXT NOT NULL CHECK (json_valid(geometry_geojson)),
    min_lon REAL NOT NULL CHECK (min_lon BETWEEN -180 AND 180),
    max_lon REAL NOT NULL CHECK (max_lon BETWEEN -180 AND 180),
    min_lat REAL NOT NULL CHECK (min_lat BETWEEN -90 AND 90),
    max_lat REAL NOT NULL CHECK (max_lat BETWEEN -90 AND 90),
    source_id TEXT NOT NULL REFERENCES data_sources(source_id) ON DELETE RESTRICT,
    observed_at TEXT,
    verified_at TEXT,
    CHECK (min_lon <= max_lon AND min_lat <= max_lat)
);

CREATE TABLE IF NOT EXISTS traffic_signs (
    sign_pk INTEGER PRIMARY KEY AUTOINCREMENT,
    sign_id TEXT NOT NULL UNIQUE,
    sign_code TEXT NOT NULL CHECK (length(sign_code) > 0),
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    bearing_degrees REAL CHECK (bearing_degrees >= 0 AND bearing_degrees < 360),
    direction TEXT NOT NULL DEFAULT 'unknown'
        CHECK (direction IN ('forward','backward','both','unknown')),
    related_segment_id TEXT,
    source_id TEXT NOT NULL REFERENCES data_sources(source_id) ON DELETE RESTRICT,
    observed_at TEXT,
    verified_at TEXT,
    FOREIGN KEY (related_segment_id) REFERENCES road_segments(segment_id)
);

CREATE INDEX IF NOT EXISTS idx_road_osm ON road_segments(osm_way_id);
CREATE INDEX IF NOT EXISTS idx_road_source ON road_segments(source_id);
CREATE INDEX IF NOT EXISTS idx_sign_code ON traffic_signs(sign_code);
CREATE INDEX IF NOT EXISTS idx_sign_source ON traffic_signs(source_id);
CREATE INDEX IF NOT EXISTS idx_sign_segment ON traffic_signs(related_segment_id);

CREATE VIRTUAL TABLE IF NOT EXISTS road_segments_rtree USING rtree(
    segment_pk, min_lon, max_lon, min_lat, max_lat
);
CREATE VIRTUAL TABLE IF NOT EXISTS traffic_signs_rtree USING rtree(
    sign_pk, min_lon, max_lon, min_lat, max_lat
);

CREATE TRIGGER IF NOT EXISTS road_segments_ai AFTER INSERT ON road_segments BEGIN
    INSERT INTO road_segments_rtree VALUES (
      new.segment_pk, new.min_lon, new.max_lon, new.min_lat, new.max_lat
    );
END;
CREATE TRIGGER IF NOT EXISTS road_segments_au AFTER UPDATE OF
min_lon,max_lon,min_lat,max_lat ON road_segments BEGIN
    DELETE FROM road_segments_rtree WHERE segment_pk=old.segment_pk;
    INSERT INTO road_segments_rtree VALUES (
      new.segment_pk, new.min_lon, new.max_lon, new.min_lat, new.max_lat
    );
END;
CREATE TRIGGER IF NOT EXISTS road_segments_ad AFTER DELETE ON road_segments BEGIN
    DELETE FROM road_segments_rtree WHERE segment_pk=old.segment_pk;
END;
CREATE TRIGGER IF NOT EXISTS traffic_signs_ai AFTER INSERT ON traffic_signs BEGIN
    INSERT INTO traffic_signs_rtree VALUES (
      new.sign_pk, new.longitude, new.longitude, new.latitude, new.latitude
    );
END;
CREATE TRIGGER IF NOT EXISTS traffic_signs_au AFTER UPDATE OF
latitude,longitude ON traffic_signs BEGIN
    DELETE FROM traffic_signs_rtree WHERE sign_pk=old.sign_pk;
    INSERT INTO traffic_signs_rtree VALUES (
      new.sign_pk, new.longitude, new.longitude, new.latitude, new.latitude
    );
END;
CREATE TRIGGER IF NOT EXISTS traffic_signs_ad AFTER DELETE ON traffic_signs BEGIN
    DELETE FROM traffic_signs_rtree WHERE sign_pk=old.sign_pk;
END;
