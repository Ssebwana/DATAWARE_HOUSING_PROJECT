# NGSIM Dataset Integration for MakFleet

## Overview

This directory contains the NGSSM (Next Generation Simulation) dataset integration for training the MakFleet ST-GNN model with real vehicle trajectory data.

## Dataset Information

**NGSIM** provides high-fidelity vehicle trajectory data including:
- Position (local X, Y coordinates)
- Speed (velocity)
- Acceleration
- Vehicle classification (motorcycle, car, truck)
- Lane information
- Preceding and following vehicle IDs

## Download Links

1. **US Government Data Portal**: https://data.transportation.gov/Automobiles/Next-Generation-Simulation-NGSIM-Vehicle-Trajector/8ect-6jqj
2. **FHWA Archive**: https://ops.fhwa.dot.gov/trafficanalysistools/ngsim.htm
3. **Kaggle Mirror**: https://www.kaggle.com/datasets/ahmed3adel/ngsim-i80-and-us101

## Directory Structure

```
data/ngsim/
├── README.md              # This file
├── raw/                   # Downloaded NGSIM raw data files
│   ├── I-80/
│   │   ├── 0750-0800.txt
│   │   ├── 0805-0815.txt
│   │   └── 0815-0830.txt
│   ├── US-101/
│   │   ├── 0750-0805.txt
│   │   ├── 0805-0815.txt
│   │   └── 0825-0835.txt
│   └── Lankershim/
│       ├── 0830-0845.txt
│       ├── 0845-0900.txt
│       └── 0900-0915.txt
└── processed/             # Processed data ready for MakFleet
    ├── telemetry.csv      # Converted telemetry data
    ├── events.csv         # Detected events from trajectories
    └── metadata.json      # Processing metadata
```

## Vehicle Classes in NGSIM

| Code | Description | MakFleet Equivalent |
|------|-------------|---------------------|
| 1    | Motorcycle  | Bodaboda |
| 2    | Passenger Car | Car/Taxi |
| 3    | Other      | Other vehicles |
| 4    | Heavy Truck | Truck |

## Processing Pipeline

1. **Parse**: Extract trajectory data from NGSIM format
2. **Transform**: Convert local coordinates to GPS, map to MakFleet schema
3. **Load**: Insert into PostgreSQL database
4. **Train**: Use for ST-GNN model training

## Usage

```bash
# 1. Download NGSIM data and place in data/ngsim/raw/

# 2. Run the processing pipeline
python data_pipeline/ngsim_pipeline.py --input data/ngsim/raw/I-80/ --output data/ngsim/processed/

# 3. Load into database
python data_pipeline/ngsim_loader.py --input data/ngsim/processed/telemetry.csv

# 4. Train ST-GNN model with NGSIM data
python ai_models/train_with_ngsim.py
```

## Data Schema Mapping

| NGSIM Field | MakFleet Table | MakFleet Column | Transformation |
|-------------|----------------|-----------------|----------------|
| Local X | telemetry | longitude | Convert to GPS + offset |
| Local Y | telemetry | latitude | Convert to GPS + offset |
| v_Vel | telemetry | speed | Direct (ft/s → km/h) |
| v_Acc | telemetry | acceleration | Direct (ft/s² → m/s²) |
| Vehicle_ID | telemetry | vehicle_id | Map to synthetic vehicle |
| Frame_ID | telemetry | timestamp | Calculate from frame rate |
| Lane_ID | telemetry | semantic_context | Store as JSON context |
| Prec_Veh_ID | events | causal_factors | Vehicle interaction |
| Following_Veh_ID | events | causal_factors | Vehicle interaction |
| Veh_Class | vehicles | model_category | Map to vehicle type |

## Coordinate Transformation

NGSIM uses local coordinates (feet from reference point). We convert to GPS using:

1. Reference point (known GPS coordinates for each site)
2. Rotation angle (road orientation)
3. Scale factor (feet to meters)

### Reference Points

| Site | Latitude | Longitude | Rotation |
|------|----------|-----------|----------|
| I-80 | 37.9372 | -122.2608 | 52.5° |
| US-101 | 34.0522 | -118.2437 | 38.2° |
| Lankershim | 34.1508 | -118.3742 | 15.8° |

## License

NGSIM data is in the public domain (US Government work).
MakFleet integration code is licensed under the project's license.