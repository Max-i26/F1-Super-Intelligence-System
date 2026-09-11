# F1 Super Intelligence — Master Project Specification

## 1. Project Identity

**Project name:** F1 Super Intelligence  
**Repository / working name:** `2025-F1-Intelligence`

### Core idea

Build a production-grade Formula 1 intelligence platform that combines:

1. Deep historical analysis of the complete 2025 F1 season.
2. Driver, race, team, tyre, strategy, telemetry, and championship intelligence.
3. External race variables such as safety cars, yellow/red flags, weather, penalties, pit stops, and race-control events.
4. OpenF1 telemetry and timing data.
5. Explainable analytical models rather than black-box predictions.
6. A premium, futuristic, highly interactive visualization layer.
7. A foundation that can later evolve toward near-real-time AI telemetry intelligence.

The system must **augment human race-engineering expertise, not pretend to replace it**.

The central philosophy is:

> **Historical context + telemetry + race context + statistical intelligence + explainable AI = F1 Super Intelligence**

The project must not be a basic Streamlit dashboard. It should feel like an **F1 Intelligence OS / race-engineering analytics platform**.

---

# 2. Product Vision

Create a system capable of answering questions such as:

- Who was actually fastest?
- Who improved or declined throughout the season?
- Which drivers were most consistent?
- Which drivers extracted more performance from difficult conditions?
- How did tyre compounds affect pace?
- How did stint length affect degradation?
- Which strategies worked?
- Which strategies failed?
- How did safety cars and yellow/red flags alter races?
- How did weather influence performance?
- Which drivers gained/lost positions?
- How did each driver's race pace evolve?
- How did championship momentum change?
- Which drivers performed above/below their season baseline?
- What happened immediately before a major performance drop?
- Can telemetry reveal unusual behavior?
- Can we identify patterns associated with tyre degradation or possible mechanical anomalies?
- Can historical context explain a live telemetry event?
- Can the system generate an evidence-backed race summary?

The platform should move from:

**Data → Analysis → Context → Intelligence → Explainability → Decision Support**

---

# 3. Important Design Principle

Do NOT build a system that claims:

> "AI can perfectly predict what a driver will do."

Human drivers make decisions under pressure, emotion, uncertainty, changing track conditions, team instructions, and unexpected events.

Telemetry cannot directly measure a driver's "heart", courage, fear, motivation, or intent.

Therefore:

- Analyze observable behavior.
- Quantify measurable patterns.
- Identify anomalies.
- Estimate probabilities where appropriate.
- Show uncertainty.
- Explain why a conclusion was reached.
- Never present speculation as fact.

The system should say:

> "Telemetry shows a significant change in braking behavior."

Not:

> "The driver became nervous."

---

# 4. Current Data Situation

The current local dataset is:

`data/2025/processed/season_laps.csv`

Current observed characteristics:

- 25,721 data rows
- 9 columns
- 21 drivers
- 10 teams
- 23 race labels

Columns:

```text
Driver
Team
LapNumber
LapTime
Compound
Stint
Position
Race
Year
```

Example:

```text
PIA,McLaren,1.0,98.693,SOFT,1.0,1.0,Bahrain,2025
```

## Important

The official 2025 calendar contains **24 rounds**, while the current dataset contains only 23 race labels.

The expected 2025 calendar order is:

1. Australia
2. China
3. Japan
4. Bahrain
5. Saudi Arabia
6. Miami
7. Imola
8. Monaco
9. Spain
10. Canada
11. Austria
12. Silverstone
13. Belgium
14. Hungary
15. Netherlands
16. Italy
17. Azerbaijan
18. Singapore
19. USA
20. Mexico
21. Brazil
22. Las Vegas
23. Qatar
24. Abu Dhabi

The missing race must be investigated rather than silently ignored.

Also distinguish:

- Miami
- USA / Austin
- Las Vegas

They are different 2025 events.

---

# 5. Data Quality First

Before intelligence is calculated, build a strong data-quality layer.

Every dataset should be audited for:

- Row count
- Column count
- Required columns
- Missing values
- Duplicate rows
- Invalid data types
- Impossible lap times
- Impossible positions
- Invalid lap numbers
- Invalid stints
- Unknown tyre compounds
- Unknown drivers
- Unknown teams
- Unexpected races
- Missing expected races
- Driver participation
- Team participation
- Race completeness
- Suspicious outliers

Current audit findings include approximately:

- LapTime missing: 316
- Compound missing: 411
- Stint missing: 354
- Position missing: 29
- Duplicate rows: 0

The audit layer must remain visible in the UI.

Never hide data-quality problems.

---

# 6. Architecture

Use a modular architecture.

Recommended structure:

```text
2025-F1-Intelligence/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   └── 2025/
│       ├── raw/
│       ├── processed/
│       │   └── season_laps.csv
│       │
│       ├── intelligence/
│       │   ├── race_intelligence.csv
│       │   ├── driver_evolution.csv
│       │   ├── driver_profiles.csv
│       │   ├── championship_snapshots.csv
│       │   ├── telemetry_features.csv
│       │   └── anomaly_events.csv
│       │
│       └── external/
│
├── src/
│   ├── data/
│   │   ├── local.py
│   │   ├── openf1.py
│   │   ├── validation.py
│   │   └── normalization.py
│   │
│   ├── intelligence/
│   │   ├── engine.py
│   │   ├── championship.py
│   │   ├── driver.py
│   │   ├── race.py
│   │   ├── strategy.py
│   │   ├── tyres.py
│   │   ├── telemetry.py
│   │   ├── anomalies.py
│   │   └── context.py
│   │
│   ├── models/
│   │   ├── degradation.py
│   │   ├── anomaly_detection.py
│   │   ├── performance.py
│   │   └── forecasting.py
│   │
│   ├── ui/
│   │   ├── theme.py
│   │   ├── components.py
│   │   ├── charts.py
│   │   └── pages.py
│   │
│   └── utils/
│       ├── logging.py
│       ├── caching.py
│       └── metrics.py
│
├── scripts/
│   ├── audit_season.py
│   ├── build_race_intelligence.py
│   ├── build_driver_evolution.py
│   ├── build_driver_profiles.py
│   ├── build_championship.py
│   ├── ingest_openf1.py
│   └── smoke_test.py
│
└── tests/
    ├── test_data.py
    ├── test_driver_metrics.py
    ├── test_race_metrics.py
    ├── test_championship.py
    ├── test_strategy.py
    └── test_telemetry.py
```

Keep computation outside `app.py`.

---

# 7. Technology Stack

Primary:

- Python
- Pandas
- NumPy
- Scikit-learn
- Streamlit
- Plotly
- Requests
- Hugging Face / PyTorch only when genuinely needed for ML components

Potential future:

- XGBoost / LightGBM
- PyTorch
- MLflow
- DuckDB
- Polars
- PostgreSQL
- Redis
- FastAPI
- WebSocket
- Docker
- GitHub Actions

Do not introduce dependencies without a reason.

---

# 8. Data Sources

## Local data

Use the existing processed 2025 lap dataset as the baseline.

## OpenF1

Use OpenF1 for richer historical F1 information.

Potential endpoints include:

- Sessions
- Drivers
- Laps
- Car data
- Positions
- Stints
- Pit stops
- Weather
- Race control
- Session results
- Championship drivers
- Championship teams
- Intervals
- Team radio

OpenF1 telemetry can provide information such as:

- Speed
- Throttle
- Brake
- RPM
- Gear
- Position

Race control can provide:

- Green flag
- Yellow flag
- Double yellow
- Safety car
- Chequered flag
- Session status
- Incidents

---

# 9. Championship Truth Layer

This is CRITICAL.

Never use:

- pace score
- driver score
- performance index
- consistency score
- arbitrary weighted metric

as official championship points.

Official championship standings must be kept separate from analytical intelligence.

Use validated championship data.

Store:

```text
Driver
RaceRound
Race
Points
CumulativePoints
Rank
```

Potential OpenF1 fields:

```text
points_current
points_start
position_current
position_start
```

The UI must clearly distinguish:

### Official / Ground Truth

from

### Analytical Intelligence

For example:

> Championship Position: 2nd

is official.

Whereas:

> Performance Intelligence Score: 94.2

is analytical.

Never confuse the two.

For the 2025 final standings, validate that:

1. Lando Norris — Champion
2. Max Verstappen — 2nd
3. Oscar Piastri — 3rd

Do not infer this from pace.

---

# 10. Race Intelligence Layer

For every Grand Prix calculate:

## Race-level

- Number of laps
- Drivers
- Teams
- Fastest lap
- Median lap
- Mean representative pace
- Pace spread
- Position changes
- Winner
- Podium
- DNF indicators if available
- Pit stops
- Safety-car periods
- Yellow flags
- Red flags
- Weather conditions
- Track conditions
- Tyre usage
- Strategy distribution

## Driver-level race metrics

For every driver:

- Best lap
- Representative pace
- Median pace
- Pace variability
- Starting position if available
- Finishing position
- Position gain/loss
- Stints
- Tyre compounds
- Stint lengths
- Pit-stop count
- Race pace trend
- Late-race performance
- Degradation estimate
- Incident exposure
- Performance vs teammate

---

# 11. Driver Intelligence

Build a complete profile for every driver.

Example profile:

```text
Driver
Team
Races
Laps
Best Pace
Representative Pace
Average Pace
Consistency
Average Position
Best Finish
Worst Finish
Average Position Gain
Momentum
Tyre Usage
Strategy Profile
Teammate Delta
Race Pace Trend
Championship Trend
```

Do not create a single magical score without explanation.

If a composite score is used, expose its components.

Example:

```text
Performance Index
├── Pace
├── Consistency
├── Position Gain
├── Race Management
├── Tyre Efficiency
└── Context-adjusted Performance
```

---

# 12. Driver Evolution Engine

Track every driver across all rounds.

For each race calculate:

- Pace
- Position
- Finish
- Position delta
- Consistency
- Tyre performance
- Teammate delta
- Strategy efficiency
- Championship points
- Cumulative championship points

Then generate:

## Growth/Fall

Visualize:

```text
Race 1 → Race 2 → Race 3 → ... → Race 24
```

For each driver.

The UI should allow:

- Select driver
- Select metric
- Compare multiple drivers
- Highlight major improvements
- Highlight major declines
- Annotate major race events

---

# 13. Pace Intelligence

Do not simply use raw average lap time.

Build robust representative pace.

Potential approach:

1. Remove invalid laps.
2. Filter obvious outliers.
3. Exclude pit-in/pit-out laps where identifiable.
4. Account for safety-car periods where possible.
5. Compare same compound where appropriate.
6. Use median / trimmed mean.
7. Compare within race.
8. Normalize across races if necessary.

Metrics:

- Median lap time
- Trimmed mean
- Best representative lap
- Standard deviation
- Interquartile range
- Pace delta
- Pace percentile

---

# 14. Tyre Intelligence

For each driver/stint:

- Compound
- Stint number
- Stint length
- Starting lap
- Ending lap
- Representative pace
- Pace evolution
- Degradation slope
- Performance drop
- Compound comparison

Example:

```text
SOFT
Lap 1 → 1:31.2
Lap 2 → 1:31.5
Lap 3 → 1:31.8
...
Lap 15 → 1:34.2
```

Estimate degradation carefully.

Do not label every slower lap as tyre degradation.

Possible causes:

- Traffic
- Safety car
- Fuel
- Track evolution
- Driver management
- Damage
- Weather
- Strategy
- Blue flags

Therefore degradation must be **context-aware**.

---

# 15. Strategy Intelligence

Analyze:

- One-stop
- Two-stop
- Three-stop
- Compound sequences
- Stint lengths
- Pit windows
- Undercut opportunities
- Overcut opportunities
- Safety-car pit opportunities
- Weather-driven strategy changes

Possible representation:

```text
Driver
→ Lap 1–18: MEDIUM
→ Lap 19–40: HARD
→ Lap 41–57: MEDIUM
```

Then compare against competitors.

Calculate:

- Strategy duration
- Pace achieved
- Position change
- Expected vs observed outcome
- Strategy efficiency

Do not claim causation unless supported by evidence.

---

# 16. External Race Context

This is one of the most important differentiators.

Integrate:

## Race control

- Safety car
- Virtual safety car if available
- Yellow flags
- Double yellows
- Red flags
- Restarts
- Track status

## Weather

- Air temperature
- Track temperature
- Humidity
- Pressure
- Wind
- Rain indicators

## Pit stops

- Number
- Duration
- Timing
- Position before/after

## Penalties

Where available:

- Driver
- Lap
- Penalty type
- Time penalty
- Grid penalty
- Result impact

The system should allow a user to see:

> "Performance dropped 1.8% during this period."

and then:

> "Context: Safety Car / wet track / tyre transition."

This creates intelligence instead of simple visualization.

---

# 17. Telemetry Intelligence

Use OpenF1 telemetry when available.

For every selected driver/session:

- Speed
- Throttle
- Brake
- RPM
- Gear
- Track position
- Lap
- Sector
- Time

Visualize:

### Speed trace

```text
Distance → Speed
```

### Throttle trace

```text
Distance → Throttle %
```

### Brake trace

```text
Distance → Brake
```

### Gear trace

```text
Distance → Gear
```

### 3D telemetry

Potentially:

```text
X
Y
Speed
```

or:

```text
Track X
Track Y
Time
```

Use Plotly 3D carefully.

The visual must add analytical value, not just look cool.

---

# 18. Driving Style Analysis

Compare drivers using measurable telemetry features.

Possible features:

- Average braking point
- Maximum braking intensity
- Brake release rate
- Throttle application rate
- Corner exit speed
- Minimum corner speed
- Acceleration profile
- Gear usage
- Speed variance
- Straight-line speed
- Cornering behavior

Then cluster drivers.

Possible outputs:

```text
Aggressive Braker
Smooth Accelerator
Late Braker
High Corner Speed
Strong Traction
Top-Speed Oriented
```

These are analytical labels.

Do not treat them as psychological/personality judgments.

---

# 19. Anomaly Detection

Build a telemetry/race anomaly engine.

Potential anomalies:

- Sudden speed drop
- Unusual throttle behavior
- Unusual braking
- RPM anomaly
- Gear anomaly
- Lap-time deviation
- Sector-time deviation
- Tyre performance collapse
- Unexpected pit behavior
- Sudden position loss

For every anomaly store:

```text
Timestamp
Driver
Race
Lap
Metric
Observed Value
Expected Value
Deviation
Severity
Possible Context
Confidence
```

Example:

```text
HIGH
Lap 42
Speed dropped 23 km/h below baseline
Possible context:
- yellow flag
- traffic
- tyre degradation
- mechanical issue
```

Never state:

> "Engine failure detected"

unless the data truly supports it.

Instead:

> "Telemetry anomaly consistent with a possible mechanical or operational issue."

---

# 20. Mechanical Failure Intelligence

This is a future advanced module.

Goal:

Detect patterns that may precede component problems.

Potential signals:

- RPM behavior
- Speed loss
- Throttle response
- Gear anomalies
- Temperature
- Lap-time degradation
- Sudden performance shifts
- Radio / race-control context if available

Approach:

1. Establish normal baseline.
2. Detect deviations.
3. Compare against historical patterns.
4. Check environmental context.
5. Check race-control context.
6. Assign anomaly score.
7. Provide possible explanations.
8. Show confidence.

Do not make unsupported failure claims.

---

# 21. Tire Degradation Model

Future ML model:

Inputs:

```text
Compound
Stint age
Lap number
Track temperature
Air temperature
Fuel proxy
Traffic
Safety car state
Driver
Team
Track
Historical pace
```

Target:

```text
Expected lap-time degradation
```

Possible models:

- Linear regression baseline
- Random Forest
- Gradient Boosting
- XGBoost
- LightGBM
- Temporal neural model if justified

Start simple.

Compare models using:

- MAE
- RMSE
- R²
- Cross-validation

Avoid leakage.

---

# 22. Performance Forecasting

Potential future predictions:

- Expected pace
- Expected degradation
- Strategy outcome probability
- Position-change probability
- Stint performance

Always provide:

- Prediction
- Confidence
- Uncertainty
- Inputs
- Model version

Example:

```text
Expected stint pace:
1:31.84 ± 0.42 sec

Confidence:
Medium

Main factors:
- tyre age
- compound
- track temperature
- historical pace
```

---

# 23. Explainable Intelligence

Every important model output should answer:

### What happened?

### Why does the system think it happened?

### What evidence supports it?

### How confident is the system?

Example:

```text
Pace deterioration detected

Evidence:
• +1.7 sec/lap over baseline
• tyre age increased from 8 → 19 laps
• track temperature increased
• no safety-car period detected
• teammate degradation was lower

Confidence: Medium-High
```

This is much stronger than:

> "AI predicts tyre failure."

---

# 24. Championship Intelligence

The Championship page should include:

## Official

- Current/final standings
- Points
- Rank
- Race-by-race points
- Cumulative points

## Analytical

- Momentum
- Pace trend
- Consistency
- Performance trend
- Position trend
- Race win rate
- Podium rate
- Teammate comparison

Visualizations:

- Championship progression
- Points gap
- Rank evolution
- Driver momentum
- Race-by-race performance matrix

Again:

**Official points must never be replaced by analytical scores.**

---

# 25. Team Intelligence

For each constructor:

- Driver performance
- Average pace
- Best pace
- Reliability indicators
- Strategy
- Pit performance
- Tyre performance
- Championship points
- Driver comparison
- Team development trend

Potential visual:

```text
Team
├── Driver A
├── Driver B
├── Pace
├── Strategy
├── Reliability
└── Championship
```

---

# 26. Teammate Intelligence

This is highly valuable.

Compare teammates on:

- Qualifying pace if available
- Race pace
- Best lap
- Median pace
- Position
- Finish
- Position gain
- Tyre management
- Stint performance
- Strategy
- Championship points

Use teammate-normalized deltas.

This reduces some track-specific bias.

---

# 27. Race Replay / Timeline

Build a race timeline.

Example:

```text
Lap 1
↓
Lap 8 — Yellow Flag
↓
Lap 14 — Pit Stop
↓
Lap 27 — Safety Car
↓
Lap 29 — Restart
↓
Lap 42 — Tyre degradation spike
↓
Lap 57 — Finish
```

Allow clicking an event to update charts.

This can become one of the platform's signature features.

---

# 28. Command Center UI

The main dashboard should feel like a professional intelligence console.

Possible layout:

```text
┌────────────────────────────────────────────────────────────┐
│ F1 SUPER INTELLIGENCE                    2025 SEASON       │
├────────────────────────────────────────────────────────────┤
│ 24 ROUNDS │ 20 DRIVERS │ 10 TEAMS │ DATA HEALTH           │
├────────────────────────────────────────────────────────────┤
│ CHAMPION          FASTEST DRIVER        BEST CONSISTENCY   │
│ Lando Norris      ...                   ...                │
├────────────────────────────────────────────────────────────┤
│ CHAMPIONSHIP EVOLUTION                                    │
├────────────────────────────────────────────────────────────┤
│ DRIVER MOMENTUM                                           │
├────────────────────────────────────────────────────────────┤
│ RACE INTELLIGENCE                                         │
├────────────────────────────────────────────────────────────┤
│ TELEMETRY / ANOMALIES / STRATEGY                          │
└────────────────────────────────────────────────────────────┘
```

---

# 29. Dashboard Pages

Minimum pages:

## 1. Command Center

Season overview.

## 2. Race Intelligence

Deep analysis of a selected Grand Prix.

## 3. Driver Intelligence

Complete driver profile.

## 4. Championship

Official standings + analytical trends.

## 5. Strategy & Tires

Stints, degradation, strategies.

## 6. Telemetry Lab

OpenF1 telemetry exploration.

## 7. Team Intelligence

Constructor analysis.

## 8. Anomaly Center

Telemetry/race anomalies.

## 9. Race Replay

Timeline-based exploration.

## 10. Data Audit

Data quality and source health.

---

# 30. Visual Design

Design language:

**Black / Gold / Dark Futuristic**

Characteristics:

- Near-black background
- Gold accents
- White typography
- Subtle red/orange warning states
- High contrast
- Minimal unnecessary decoration
- Premium motorsport aesthetic

Avoid:

- Generic Streamlit look
- Excessive neon
- Excessive particles
- Decorative 3D without purpose
- Cluttered dashboards

Charts should be:

- Clean
- Interactive
- Tooltipped
- Consistent
- High information density
- Responsive

---

# 31. Signature Visualizations

Build standout visuals.

### Championship spiral / progression

Show championship position changes across rounds.

### Driver trajectory

Performance over time.

### Race pace battle

Two or more drivers' pace curves.

### Tyre degradation curves

Pace vs tyre age.

### Strategy timeline

Compound and stint changes.

### Track telemetry map

Track position + speed.

### Driver radar

Use carefully and normalize correctly.

### Performance heatmap

Driver × Race.

### Anomaly timeline

Race lap × anomaly severity.

### Team development chart

Performance across season.

---

# 32. Data Pipeline

Recommended pipeline:

```text
Raw Data
   ↓
Ingestion
   ↓
Validation
   ↓
Normalization
   ↓
Feature Engineering
   ↓
Race Intelligence
   ↓
Driver Intelligence
   ↓
Telemetry Intelligence
   ↓
Championship Truth
   ↓
ML Models
   ↓
Explainability
   ↓
Dashboard
```

Every stage should be reproducible.

---

# 33. Caching

Use caching for:

- OpenF1 requests
- Processed datasets
- Expensive feature calculations
- Model loading

Do not repeatedly download the same data.

Use sensible cache invalidation.

---

# 34. API Reliability

OpenF1 requests should include:

- Timeout
- Retry
- Error handling
- Rate-limit awareness
- Caching
- Logging
- Clear UI errors

Never crash the entire dashboard because one API endpoint fails.

Example:

```text
OpenF1 telemetry unavailable.

Local historical analysis remains available.
```

---

# 35. Offline-First Principle

The platform should remain useful even if OpenF1 is unavailable.

Local analysis:

- Race metrics
- Driver metrics
- Strategy
- Tyres
- Championship snapshots already stored
- Historical trends

should work without network access.

Online enrichment:

- Telemetry
- Race control
- Weather
- Additional timing

can be optional.

---

# 36. Configuration

Use one central configuration file.

Example:

```python
RACES_2025 = [
    "Australia",
    "China",
    "Japan",
    "Bahrain",
    "Saudi Arabia",
    "Miami",
    "Imola",
    "Monaco",
    "Spain",
    "Canada",
    "Austria",
    "Silverstone",
    "Belgium",
    "Hungary",
    "Netherlands",
    "Italy",
    "Azerbaijan",
    "Singapore",
    "USA",
    "Mexico",
    "Brazil",
    "Las Vegas",
    "Qatar",
    "Abu Dhabi",
]
```

Keep URLs, paths, thresholds, and model parameters centralized.

---

# 37. Testing

Create tests for:

## Data

- Required columns
- Missing values
- Duplicate handling
- Invalid rows

## Metrics

- Pace
- Position gain
- Consistency
- Momentum

## Championship

- Points ordering
- Cumulative points
- Rank ordering
- Official vs analytical separation

## Strategy

- Stint construction
- Compound transitions
- Missing stint values

## Telemetry

- Missing fields
- Timestamp ordering
- Driver filtering

## API

Mock API responses.

Do not rely on live API calls for unit tests.

---

# 38. Quality Gates

Before declaring a module complete:

- No syntax errors
- No obvious runtime errors
- No unhandled NaN failures
- No silent data loss
- No duplicated calculations
- No incorrect championship logic
- No fake official data
- No unexplained scores
- No hardcoded driver assumptions
- No race-order assumptions based on dataset sorting
- No hidden API dependency
- No broken visualizations

---

# 39. Performance

Optimize for:

- Large telemetry datasets
- Fast filtering
- Cached computations
- Vectorized Pandas/NumPy
- Avoid unnecessary loops
- Avoid repeated CSV reads
- Avoid repeated API requests
- Lazy loading for expensive pages

If the data grows significantly:

Consider:

- Parquet
- DuckDB
- Polars
- PostgreSQL

---

# 40. Reproducibility

Every generated intelligence dataset should ideally record:

```text
GeneratedAt
Source
SourceVersion
DataVersion
ModelVersion
ConfigurationVersion
```

This makes results auditable.

---

# 41. Auditability

For every intelligence result, allow tracing back to:

```text
Result
↓
Feature
↓
Source Data
↓
Race
↓
Lap
↓
Telemetry / timing event
```

This is essential for a serious engineering-oriented platform.

---

# 42. ML Development Philosophy

Do not jump directly to deep learning.

Build in stages:

### Level 1

Rule-based analytics.

### Level 2

Statistical baselines.

### Level 3

Classical ML.

### Level 4

Advanced ML.

### Level 5

Deep learning / temporal models.

Each model must beat a baseline before being adopted.

---

# 43. Model Evaluation

Use appropriate metrics.

Regression:

- MAE
- RMSE
- R²

Classification:

- Accuracy
- Precision
- Recall
- F1
- ROC-AUC
- PR-AUC

Anomaly detection:

- Precision
- Recall
- False positive rate
- Detection latency

Do not optimize solely for accuracy.

---

# 44. Leakage Prevention

Be extremely careful.

Do not use future race information to predict an earlier race.

For example:

Bad:

```text
Predict Bahrain using data from Monaco.
```

Good:

```text
Predict Bahrain using information available before/during Bahrain.
```

For historical evaluation use:

- Time-based splits
- Race-based validation
- Walk-forward validation

---

# 45. Real-Time Future Architecture

Future system:

```text
F1 Data Stream
       ↓
Ingestion Gateway
       ↓
Message Queue
       ↓
Feature Engine
       ↓
Real-Time Intelligence Engine
       ↓
Anomaly Detection
       ↓
Strategy Engine
       ↓
Alert Engine
       ↓
Dashboard / Engineer Interface
```

Potential technologies:

- FastAPI
- WebSockets
- Kafka / Redpanda
- Redis
- PostgreSQL
- DuckDB
- Docker

Do not build this before the historical foundation is stable.

---

# 46. Real-Time Alerts

Future examples:

```text
⚠ TYRE DEGRADATION
Driver: XXX
Lap: 37
Observed degradation: +0.82 sec/lap
Confidence: High
```

```text
⚠ TELEMETRY ANOMALY
Driver: XXX
Lap: 42
Speed deficit: 21 km/h
Possible context:
- traffic
- yellow flag
- mechanical anomaly
```

```text
🟡 STRATEGY OPPORTUNITY
Safety Car detected
Potential pit window opened
```

Alerts must be evidence-based.

---

# 47. Human-in-the-Loop Design

The system should support an engineer or analyst.

The UI should provide:

- Evidence
- Context
- Confidence
- Alternatives
- Historical comparison
- Raw data access

The user remains the decision maker.

---

# 48. Collaboration Architecture

The project should support collaboration with another F1/AI developer.

Use clear module boundaries:

### Historical analytics

Your main area.

### Telemetry intelligence

Collaborator / joint area.

### ML models

Joint.

### Visualization

Joint.

### Data engineering

Joint.

### Documentation

Joint.

Avoid huge single files.

Use:

- Git branches
- Pull requests
- Issues
- Feature branches
- Clear commit messages
- Module ownership

---

# 49. Recommended Git Workflow

Example:

```text
main
│
├── feature/race-intelligence
├── feature/telemetry
├── feature/championship
├── feature/driver-evolution
├── feature/anomaly-detection
└── feature/ui
```

Each feature should include:

- Code
- Tests
- Documentation
- Sample output

---

# 50. Documentation

README must explain:

1. What the project is.
2. Why it exists.
3. Architecture.
4. Data sources.
5. Data limitations.
6. How to install.
7. How to run.
8. How the intelligence works.
9. Model evaluation.
10. Screenshots.
11. API usage.
12. Reproducibility.
13. Limitations.
14. Roadmap.
15. Contributors.

Do not hide limitations.

---

# 51. Roadmap

## Phase 1 — Foundation

- [x] Project structure
- [x] Local dataset
- [x] Data audit
- [x] Driver profiles
- [x] Race intelligence foundation
- [x] Driver evolution foundation
- [x] Basic Streamlit architecture

## Phase 2 — Championship Truth

- [ ] Official 2025 championship ingestion
- [ ] Race-by-race championship snapshots
- [ ] Correct final standings
- [ ] Constructor standings
- [ ] Official vs analytical separation

## Phase 3 — Complete 2025 Intelligence

- [ ] Fix missing Azerbaijan data
- [ ] Normalize all race names
- [ ] Complete 24-round dataset
- [ ] Race summaries
- [ ] Driver summaries
- [ ] Team summaries
- [ ] Growth/fall analysis

## Phase 4 — External Context

- [ ] Race control
- [ ] Safety car
- [ ] Yellow/red flags
- [ ] Weather
- [ ] Pit stops
- [ ] Penalties
- [ ] Context-aware analysis

## Phase 5 — Telemetry Lab

- [ ] Speed
- [ ] Throttle
- [ ] Brake
- [ ] RPM
- [ ] Gear
- [ ] Track position
- [ ] 3D visualization
- [ ] Driver comparison

## Phase 6 — Intelligence

- [ ] Tyre degradation
- [ ] Anomaly detection
- [ ] Driving style analysis
- [ ] Strategy intelligence
- [ ] Mechanical anomaly research
- [ ] Explainability layer

## Phase 7 — Advanced ML

- [ ] Baseline models
- [ ] Classical ML
- [ ] Time-series models
- [ ] Model evaluation
- [ ] Walk-forward validation
- [ ] Model registry

## Phase 8 — Real-Time

- [ ] Streaming ingestion
- [ ] WebSocket
- [ ] Real-time features
- [ ] Real-time anomaly detection
- [ ] Strategy alerts
- [ ] Engineer dashboard

---

# 52. Current MVP Components

Current MVP should contain:

```text
app.py
config.py
requirements.txt

src/
  data/
    local.py
    openf1.py

  intelligence/
    engine.py
    championship.py

  ui/
    theme.py

scripts/
  smoke_test.py
```

Current views:

- Command Center
- Race Intelligence
- Driver Intelligence
- Championship
- Strategy & Tires
- Telemetry Lab
- Data Audit

---

# 53. Current Known Issues to Fix

## Issue 1 — Incomplete calendar

Current dataset has 23 races.

Expected: 24.

Investigate Azerbaijan.

## Issue 2 — Race naming

Ensure:

```text
Miami
USA / Austin
Las Vegas
```

are distinct.

## Issue 3 — Championship source

Never use analytical Score as official championship points.

## Issue 4 — Championship ranking

Final 2025 ranking must be validated against official championship data.

Expected:

```text
1. Lando Norris
2. Max Verstappen
3. Oscar Piastri
```

## Issue 5 — Intelligence output paths

Keep generated intelligence datasets consistently under:

```text
data/2025/intelligence/
```

or deliberately support a documented compatibility path.

Do not randomly mix:

```text
processed/
```

and

```text
intelligence/
```

for the same type of output.

## Issue 6 — Missing values

Never convert NaN positions directly to integer.

Always handle:

```python
pd.isna(value)
```

before integer conversion.

## Issue 7 — Streamlit execution

Run Streamlit through its proper Streamlit launcher, not as:

```text
python app.py
```

---

# 54. Definition of Done

The project is NOT finished when:

- Dashboard opens.
- Charts exist.
- Accuracy number exists.
- Streamlit works.

It is finished when:

### Data

- Complete season
- Audited
- Reproducible
- Source documented

### Analytics

- Race intelligence
- Driver intelligence
- Team intelligence
- Championship intelligence
- Strategy
- Tyres
- Telemetry
- External context

### ML

- Baselines
- Proper validation
- No leakage
- Explainability
- Confidence

### UI

- Premium
- Fast
- Interactive
- Clear
- Consistent

### Engineering

- Modular
- Tested
- Logged
- Cached
- Error tolerant
- Versioned

### Documentation

- Full README
- Architecture
- Data dictionary
- Model documentation
- Limitations
- Roadmap

---

# 55. Ultimate Product Concept

The final product should feel like:

> **A digital race engineer's intelligence workstation.**

Not:

> "A Streamlit F1 dashboard."

A user should be able to open one race and move through:

```text
RACE
 ↓
RESULT
 ↓
PACE
 ↓
TYRES
 ↓
STRATEGY
 ↓
TELEMETRY
 ↓
RACE CONTROL
 ↓
WEATHER
 ↓
ANOMALIES
 ↓
DRIVER BEHAVIOR
 ↓
CHAMPIONSHIP IMPACT
```

And for one driver:

```text
DRIVER
 ↓
SEASON PROFILE
 ↓
RACE-BY-RACE EVOLUTION
 ↓
PACE
 ↓
CONSISTENCY
 ↓
TYRES
 ↓
STRATEGY
 ↓
TEAMMATE DELTA
 ↓
TELEMETRY
 ↓
ANOMALIES
 ↓
CHAMPIONSHIP
```

---

# 56. Master Development Rule

Whenever adding a new feature, ask:

1. Does it use reliable data?
2. Is the metric mathematically defensible?
3. Is there a baseline?
4. Can the result be explained?
5. Can it be validated?
6. Does it distinguish correlation from causation?
7. Does it handle missing data?
8. Does it avoid leakage?
9. Does it improve the intelligence of the system?
10. Does it make the platform more useful to an F1 analyst?

If the answer is no, do not add the feature merely because it looks impressive.

---

# 57. Master Prompt for AI Coding Agents

Use the following prompt when giving this project to an AI coding agent:

> You are working on a production-grade Formula 1 intelligence platform called **F1 Super Intelligence**, repository name `2025-F1-Intelligence`.
>
> The goal is to build an F1 Intelligence OS rather than a basic dashboard. The platform combines complete 2025 historical race analysis, driver evolution, championship truth, tyre and strategy intelligence, race-control context, weather, pit stops, OpenF1 telemetry, anomaly detection, explainable ML, and eventually real-time intelligence.
>
> Follow the architecture and requirements in this specification.
>
> **Core principles:**
>
> - Never invent data.
> - Never call an analytical score official championship points.
> - Never infer driver emotions or intent from telemetry.
> - Separate ground truth from analytical intelligence.
> - Prefer robust statistics over naive averages.
> - Handle NaN, missing, duplicate, invalid, and incomplete data explicitly.
> - Never silently drop important records.
> - Avoid data leakage.
> - Use time/race-based validation for predictive models.
> - Keep all important results explainable.
> - Show confidence and uncertainty.
> - Keep the application useful when OpenF1 is unavailable.
> - Cache API requests and expensive computations.
> - Keep API failures isolated.
> - Keep computation modular and outside the UI.
> - Write tests for every important analytical component.
> - Do not introduce unnecessary dependencies.
> - Optimize for performance.
> - Maintain reproducibility.
> - Document assumptions and limitations.
>
> **Current local dataset:**
>
> `data/2025/processed/season_laps.csv`
>
> Columns:
>
> `Driver, Team, LapNumber, LapTime, Compound, Stint, Position, Race, Year`
>
> Current data has 25,721 rows, 21 drivers, 10 teams, and 23 race labels. The official 2025 calendar has 24 rounds, so investigate and resolve the missing Azerbaijan race rather than treating the current dataset as complete.
>
> Expected race order:
>
> Australia, China, Japan, Bahrain, Saudi Arabia, Miami, Imola, Monaco, Spain, Canada, Austria, Silverstone, Belgium, Hungary, Netherlands, Italy, Azerbaijan, Singapore, USA, Mexico, Brazil, Las Vegas, Qatar, Abu Dhabi.
>
> **Required product areas:**
>
> - Command Center
> - Race Intelligence
> - Driver Intelligence
> - Team Intelligence
> - Championship
> - Strategy & Tires
> - Telemetry Lab
> - Anomaly Center
> - Race Replay
> - Data Audit
>
> **Required analytical layers:**
>
> - Data quality
> - Race metrics
> - Driver metrics
> - Team metrics
> - Driver evolution
> - Championship truth
> - Pace intelligence
> - Tyre intelligence
> - Strategy intelligence
> - Race-control context
> - Weather context
> - Pit-stop intelligence
> - Penalty context
> - Telemetry intelligence
> - Driving-style analysis
> - Anomaly detection
> - Explainability
> - Future predictive ML
>
> **Championship requirement:**
>
> Official championship standings must come from validated championship data such as OpenF1 championship snapshots or another authoritative source. Never calculate official championship standings from pace, consistency, or arbitrary scores.
>
> Validate the 2025 final order:
>
> 1. Lando Norris
> 2. Max Verstappen
> 3. Oscar Piastri
>
> Keep official championship data separate from analytical performance scores.
>
> **Visual requirement:**
>
> Build a premium black/gold/dark-futuristic motorsport interface. Use Plotly for interactive charts. Use 3D only where it provides meaningful telemetry insight. Avoid generic Streamlit styling, excessive decoration, and unnecessary particle effects.
>
> **Engineering requirement:**
>
> Before modifying code:
>
> 1. Inspect the existing architecture.
> 2. Identify dependencies.
> 3. Check data schemas.
> 4. Check existing generated outputs.
> 5. Avoid duplicating existing functionality.
>
> After modifying code:
>
> 1. Run syntax checks.
> 2. Run relevant tests.
> 3. Run the smoke test.
> 4. Check for NaN/runtime failures.
> 5. Verify output schemas.
> 6. Verify championship logic.
> 7. Verify dashboard views.
> 8. Report exactly what changed.
>
> Build incrementally. Do not rewrite working components unnecessarily.
>
> The end goal is a serious, explainable, production-grade F1 intelligence platform that can later evolve into a real-time telemetry intelligence system.

---

# 58. Final Success Definition

The final system should answer:

> **"What happened in an F1 race, why did it happen, how confident are we, what evidence supports it, how did it affect the driver/team/championship, and what does the telemetry reveal?"**

That is the core of **F1 Super Intelligence**.

