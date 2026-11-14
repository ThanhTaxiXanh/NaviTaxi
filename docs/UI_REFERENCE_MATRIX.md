# Three screenshot reference acceptance matrix (Phase 1)

The source files are user-supplied `IMG_4480.jpeg` (Search), `IMG_4483.jpeg` (Offline) and `IMG_4485.jpeg` (Settings). These are visual targets, not evidence of implemented real-time services. Branding uses **NaviTaxiMap** in the header and **NaviTaxi** as Android app label.

## IMG_4480 — Search

| Reference feature | Kotlin UI / state | Engine verification |
| --- | --- | --- |
| Header/logo and cream/teal rounded cards | Implemented as Compose | Android screenshot comparison pending |
| Address/place/POI text input | Local matching, accent insensitive | Full geocoding Phase 9 |
| Microphone | Android speech recognition intent | Device/provider test pending |
| Address / Place / POI tabs | Interactive filtering | POI catalog Phase 9 |
| Airport, bus, hotel, restaurant, hospital, ATM shortcuts | Interactive categories | Real POI dataset Phase 9; unsupported categories return no matches |
| Recent locations and suggestions | Screenshot reference sample entries | Persisted actual search history pending |
| Search results and place selection | Local sample entries | Live coordinate/distance lookup Phase 6/9 |
| Favorite star | Clickable state | Persistent POI favorites pending |
| Preview image | **Explicitly illustrative** | Actual map preview Phase 2 |
| View on map | Explanation of pending MapLibre feature | Phase 2 |

## IMG_4483 — Offline Maps

| Reference feature | Kotlin UI / state | Engine verification |
| --- | --- | --- |
| Phone storage/free/used bar | Real `StatFs` values | Android device test pending |
| Province / Whole Viet Nam tabs | Interactive | 34-province official catalog Phase 5 |
| Vietnam outline illustration | Clearly labeled schematic placeholder | Official sourced borders Phase 5 |
| Province search + quick suggestions | Interactive sample list | Complete metadata Phase 5 |
| Download (+) actions | Explicit missing data source notice | Real PMTiles package Phase 3–5 |
| Active downloads, progress, pause, resume, cancel | No fake active transfers shown | Phase 4 |
| Downloaded regions, update/delete | No fake packages shown | Phase 4 |
| Wi-Fi auto update / cellular permission | Persisted state | Transfer enforcement Phase 4 |

## IMG_4485 — Settings

| Reference feature | Kotlin UI / state | Engine verification |
| --- | --- | --- |
| Light/dark selection | Theme palette + persisted choice | Device screenshots pending |
| Guidance volume slider | Persisted 0–100% | TTS gain integration Phase 7 |
| Voice profile | Selectable and persisted | TTS provider integration Phase 7 |
| Map themes | Selectable and persisted | MapLibre style mapping Phase 2 |
| 3D buildings / traffic toggles | Persisted choice | Data-rendering Phase 8/10 |
| GPS economy/balanced/high | Persisted choice | Power/GPS engine Phase 6 |
| Speed limit alert | Persisted choice; no invented alerts | **Verified source data + matcher Phase 11** |
| Lane guidance | Persisted choice | Navigation Phase 7 |
| POI visibility / density | Persisted choice | Map/POI layer Phase 9 |

## Critical acceptance limitations

- Matching an iPhone mockup **100%** on Android requires target display specifications, source graphics, fonts, screenshots and instrumented pixel/layout comparison; presently **NOT VERIFIED**.
- Visual controls must not imply actual offline maps, downloaded regions, traffic, precise location or legal speed-limit data until those engines pass tests.
- Any future road-speed display must show `Không có dữ liệu` for segments without verified limits. Signs must preserve recorded WGS84 coordinates and evidence source. Both must work offline once shipped.
