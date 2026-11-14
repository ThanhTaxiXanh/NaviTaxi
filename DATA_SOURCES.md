# Data sources and evidence policy

| Domain | Current state | Planned lawful source | Validation |
| --- | --- | --- | --- |
| Road network | NOT INGESTED | OpenStreetMap extracts (ODbL) | source snapshots, attribution, geometry |
| Speed limits | NO VERIFIED RECORDS | OpenStreetMap `maxspeed` tags supplemented by independently licensed legal/sign surveys | value type/unit, source URL, direction, last verified |
| Traffic signs | NO VERIFIED RECORDS | OpenStreetMap `traffic_sign` or licensed survey GeoJSON | physical WGS84 lat/lon, sign code, direction, source and timestamp |
| Offline vector map | NOT INGESTED | licensed OSM data -> PMTiles | checksum, metadata, renderer proof |
| Local legal defaults | NOT INGESTED | official Vietnamese traffic law, date-specific applicability | legal citation and vehicle/road class; never infer site-specific signage |
| Province catalog | NOT INGESTED | official 34 provinces effective 2025-07-01 | boundaries and metadata source |
| Live traffic | NOT INGESTED | lawful provider under acceptable terms | staleness and consent |

A data source's URL and license must be recorded before its content can be shipped. OSM tags may be incomplete or outdated, so `maxspeed` cannot be silently promoted to authoritative law. A posted sign location is **not** the same as a road line centroid. No real coordinates or limits are asserted in this phase.
