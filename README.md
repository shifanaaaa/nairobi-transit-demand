# Nairobi Matatu Network — Demand, Capacity & Coverage Analysis

An estimated demand-vs-capacity analysis built on top of Nairobi's open matatu (informal transit) route data, identifying where the network is likely overloaded, underused, or has coverage gaps.

## The Problem

In most cities across the developing world — Nairobi, Lagos, Manila, and many Indian cities — the majority of motorized trips happen on informal transit: shared minibuses, matatus, tempos, and similar vehicles that don't run on fixed schedules and aren't tracked by any central system. In some cities this exceeds 90% of all trips. Because informal transit is not centrally tracked in the same way as formal transit, detailed passenger-level performance data can be difficult to obtain — city planners and NGOs have little data-driven basis for answering questions like which routes are overcrowded, where coverage is missing, or which routes may no longer be worth running.

## Existing Work This Builds On

The [Digital Matatus](https://digitalmatatus.com) project (and the wider [DigitalTransport4Africa](https://digitaltransport4africa.org) initiative) solved the hardest part of this problem: they physically rode Nairobi's matatu routes with GPS trackers and released the resulting route/stop/frequency map publicly, in GTFS format. That data tells you *where routes go* and *roughly how often vehicles run* — it does not include passenger counts or ridership data, which doesn't exist for this network in any public form.

## What This Project Adds

This project estimates the missing demand layer on top of that open route map:

1. **Capacity** — computed from GTFS service frequency × an assumed vehicle capacity (14 seats), per route and direction.
2. **Estimated demand** — a gravity model combining population (WorldPop) and points of interest (OpenStreetMap) as origin/destination weights, calibrated against a real estimate of Nairobi's daily matatu commuter volume (~3M, KIPPRA).
3. **Assignment** — both demand and capacity are assigned onto Nairobi's real road network (OpenStreetMap) via shortest-path routing, so they can be compared segment by segment.
4. **Classification** — each road segment is flagged as **overloaded**, **balanced**, **underused**, or a **coverage gap** (real estimated demand, zero matched matatu capacity), based on the demand-to-capacity (D/C) ratio.

## Data Sources

| Source | Used for | Access |
|---|---|---|
| Digital Matatus / DT4A GTFS feed | Route, stop, and frequency data (2019–2020 service) | Free download |
| WorldPop | Gridded population estimates | Free download |
| OpenStreetMap | Road network + points of interest | Free via Overpass/OSMnx |
| KIPPRA estimate | Calibration anchor (~3M daily matatu commuters) | Published estimate |

## How the Estimates Are Constructed

**Demand.** Potential transit demand is estimated using a gravity-based model combining population and points of interest. The model is calibrated against an estimated Nairobi matatu commuter volume.

**Capacity.** Route capacity is estimated from observed service frequency and an assumed vehicle capacity of 14 seats per vehicle.

**Segment classification.** Estimated demand is compared with modeled capacity using the demand-to-capacity ratio:
D/C = estimated demand ÷ modeled capacity

Segments are classified as overloaded, balanced, or underused. Areas with estimated demand but no matched transit capacity are identified as potential coverage gaps.

## Results

A sensitivity check was run comparing two demand-assignment cutoffs (top-5 vs. top-15 candidate destinations per stop):

| Classification | K=5 | K=15 |
|---|---|---|
| Overloaded | 96 | 121 |
| Balanced | 67 | 128 |
| Coverage gap | 2,838 | 5,151 |
| Underused | 10,371 | 10,285 |

The overloaded segment share was stable across both settings (1.20% → 1.34%), suggesting the identification of genuinely overloaded corridors is robust. Coverage-gap counts were more sensitive to this parameter (roughly doubling), indicating they should be treated as an indicative starting point for investigation rather than a precise count.

## Important Limitations

- The analysis estimates potential demand; it does not observe passenger boardings.
## Running the Dashboard

```bash
pip install streamlit streamlit-folium folium
streamlit run app/app.py
```

## Reproducing the Analysis

The full pipeline (data download, supply model, gravity model, network assignment, classification) is in `notebooks/analysis.ipynb`. It was built and run in Google Colab; the notebook downloads all required open data directly and requires no manual dataset preparation beyond an internet connection.

## Live Demo

[Add your Streamlit Community Cloud link here once deployed]
- Matatu route data represents 2019–2020 service and may not reflect the current network.
- Vehicle capacity is assumed rather than independently measured.
- Coverage-gap results are sensitive to the number of candidate destinations considered during demand assignment.
- Demand is assigned using all-or-nothing shortest-path routing, which can concentrate modeled flows onto fewer roads than real-world passengers would.
- An OpenStreetMap network segment is a graph edge between intersections, not necessarily a full transit route or fixed distance.

## Repository Structure

nairobi-transit-demand/
├── README.md
├── notebooks/
│ └── analysis.ipynb # full pipeline: data loading through comparison export
├── app/
│ ├── app.py # Streamlit dashboard
│ ├── comparison_k5.json # pre-computed results, K=5
│ └── comparison_k15.json # pre-computed results, K=15
└── requirements.txt

