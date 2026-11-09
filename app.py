
import streamlit as st
from streamlit_folium import st_folium
import folium
import json
from pathlib import Path
from collections import Counter


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Nairobi Matatu Network",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------

st.markdown("""
<style>
    .block-container {
        max-width: 1500px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }

    .project-title {
        font-size: 2.1rem;
        font-weight: 650;
        letter-spacing: -0.03em;
        margin-bottom: 0.15rem;
    }

    .project-subtitle {
        font-size: 0.95rem;
        color: #6b7280;
        margin-bottom: 1.8rem;
    }

    .section-title {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b7280;
        margin-top: 1.4rem;
        margin-bottom: 0.6rem;
    }

    .meta {
        font-size: 0.82rem;
        color: #6b7280;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.78rem;
        color: #6b7280;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.55rem;
        font-weight: 600;
    }

    section[data-testid="stSidebar"] {
        border-right: 1px solid #e5e7eb;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# FILE PATHS AND DATA LOADING
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent


def find_data_file(filename):
    """
    Find JSON files either beside app.py or inside
    an app/ subdirectory.
    """

    possible_paths = [
        BASE_DIR / filename,
        BASE_DIR / "app" / filename,
        BASE_DIR.parent / filename
    ]

    for path in possible_paths:
        if path.exists():
            return path

    raise FileNotFoundError(
        f"Could not find {filename}. "
        "Place the JSON file beside app.py or inside the app folder."
    )


@st.cache_data
def load_data(file_path):
    """
    Load and cache the JSON data.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    '<div class="project-title">Nairobi Matatu Network</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="project-subtitle">'
    'Demand, capacity and network coverage analysis'
    '</div>',
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.markdown("### Analysis")

    k_choice = st.selectbox(
        "Demand assignment",
        [5, 15],
        format_func=lambda x: f"Top {x} destinations"
    )

    st.markdown("---")

    st.markdown("### Map layers")

    show_network = st.checkbox(
        "Matatu network",
        value=True
    )

    show_overloaded = st.checkbox(
        "Potentially overloaded",
        value=True
    )

    show_gaps = st.checkbox(
        "Coverage gaps",
        value=True
    )

    show_underused = st.checkbox(
        "Underused",
        value=True
    )

    show_balanced = st.checkbox(
        "Balanced",
        value=False
    )

    st.markdown("---")

    st.markdown("### Classification")

    st.markdown(
        """
        <div class="meta">
        <b>Overloaded</b><br>
        Demand exceeds modeled capacity.
        <br><br>

        <b>Balanced</b><br>
        Demand and capacity are broadly aligned.
        <br><br>

        <b>Underused</b><br>
        Modeled capacity substantially exceeds demand.
        <br><br>

        <b>Coverage gap</b><br>
        Estimated demand with no matched transit capacity.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown(
        '<div class="meta">'
        '<b>Data vintage</b><br>'
        'Matatu service: 2019–2020 GTFS<br>'
        'Demand: modeled estimate'
        '</div>',
        unsafe_allow_html=True
    )


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

filename = f"comparison_k{k_choice}.json"

try:
    data_path = find_data_file(filename)
    data = load_data(str(data_path))

except FileNotFoundError as error:
    st.error(str(error))
    st.stop()

except json.JSONDecodeError:
    st.error(f"The file {filename} contains invalid JSON.")
    st.stop()


# ---------------------------------------------------------
# COUNTS
# ---------------------------------------------------------

counts = Counter(row["flag"] for row in data)

total = len(data)


# ---------------------------------------------------------
# NETWORK SUMMARY
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">Network overview</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4, c5 = st.columns(
    [1, 1, 1, 1, 1.15]
)

c1.metric(
    "Analyzed segments",
    f"{total:,}"
)

c2.metric(
    "Potentially overloaded",
    f"{counts.get('overloaded', 0):,}"
)

c3.metric(
    "Coverage gaps",
    f"{counts.get('coverage_gap', 0):,}"
)

c4.metric(
    "Underused",
    f"{counts.get('underused', 0):,}"
)

c5.metric(
    "Balanced",
    f"{counts.get('balanced', 0):,}"
)


# ---------------------------------------------------------
# MAP
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">Network map</div>',
    unsafe_allow_html=True
)


# Classification colours

colors = {
    "underused": "#377eb8",
    "balanced": "#4daf4a",
    "overloaded": "#d73027",
    "coverage_gap": "#fdae61"
}


# Classification visibility

enabled = {
    "underused": show_underused,
    "balanced": show_balanced,
    "overloaded": show_overloaded,
    "coverage_gap": show_gaps
}


# Create map

m = folium.Map(
    location=[-1.286389, 36.817223],
    zoom_start=12,
    tiles="OpenStreetMap",
    control_scale=True,
    prefer_canvas=True
)


# ---------------------------------------------------------
# PREPARE GEOJSON FEATURES
# ---------------------------------------------------------

# Instead of creating thousands of individual Folium
# PolyLine objects, collect segments into four groups.

features_by_flag = {
    "underused": [],
    "balanced": [],
    "overloaded": [],
    "coverage_gap": []
}


for row in data:

    flag = row["flag"]

    # Preserve original network visibility behaviour.
    if not show_network and flag not in (
        "overloaded",
        "coverage_gap"
    ):
        continue

    # Apply classification filters.
    if flag in enabled and not enabled[flag]:
        continue

    coords = row.get("coords", [])

    if not isinstance(coords, list) or len(coords) < 2:
        continue

    # Original coordinates are [latitude, longitude].
    # GeoJSON requires [longitude, latitude].

    geojson_coords = [
        [float(point[1]), float(point[0])]
        for point in coords
    ]

    demand = row.get(
        "estimated_demand_per_hour", 0
    ) or 0

    capacity = row.get(
        "capacity_per_hour", 0
    ) or 0

    dc_ratio = row.get("dc_ratio")

    if dc_ratio is not None:
        dc_text = f"{dc_ratio:.2f}×"
    else:
        dc_text = "N/A"

    label = flag.replace("_", " ").title()

    # Each feature carries its own tooltip information.

    feature = {
        "type": "Feature",

        "geometry": {
            "type": "LineString",
            "coordinates": geojson_coords
        },

        "properties": {
            "classification": label,
            "demand": f"{demand:.0f}",
            "capacity": f"{capacity:.0f}",
            "dc_ratio": dc_text
        }
    }

    features_by_flag[flag].append(feature)


# ---------------------------------------------------------
# ADD FOUR GEOJSON LAYERS
# ---------------------------------------------------------

layer_settings = {
    "underused": {
        "name": "Underused",
        "weight": 2.5,
        "opacity": 0.55
    },

    "balanced": {
        "name": "Balanced",
        "weight": 2.5,
        "opacity": 0.55
    },

    "overloaded": {
        "name": "Overloaded",
        "weight": 6,
        "opacity": 0.85
    },

    "coverage_gap": {
        "name": "Coverage gaps",
        "weight": 6,
        "opacity": 0.85
    }
}


for flag, features in features_by_flag.items():

    if not features:
        continue

    settings = layer_settings[flag]
    color = colors[flag]

    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }

    folium.GeoJson(
        data=feature_collection,

        name=settings["name"],

        style_function=lambda feature,
        color=color,
        weight=settings["weight"],
        opacity=settings["opacity"]: {
            "color": color,
            "weight": weight,
            "opacity": opacity
        },

        tooltip=folium.GeoJsonTooltip(
            fields=[
                "classification",
                "demand",
                "capacity",
                "dc_ratio"
            ],

            aliases=[
                "Classification:",
                "Demand (passenger-trips/hr):",
                "Capacity (passenger-spaces/hr):",
                "D/C ratio:"
            ],

            sticky=True,
            labels=True
        )
    ).add_to(m)


# ---------------------------------------------------------
# DISPLAY MAP
# ---------------------------------------------------------

st_folium(
    m,
    width=None,
    height=680,
    returned_objects=[]
)


# ---------------------------------------------------------
# LEGEND
# ---------------------------------------------------------

st.markdown("##### Map legend")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("🔴 Overloaded")

with c2:
    st.markdown("🟠 Coverage gap")

with c3:
    st.markdown("🟢 Balanced")

with c4:
    st.markdown("🔵 Underused")


# ---------------------------------------------------------
# METHODOLOGY
# ---------------------------------------------------------

tab1, tab2 = st.tabs([
    "Methodology",
    "Limitations"
])


with tab1:

    st.markdown("### How the estimates are constructed")

    st.markdown(
        """
        **Demand**

        Potential transit demand is estimated using a gravity-based
        model combining population and points of interest. The model
        is calibrated against an estimated Nairobi matatu commuter
        volume.

        **Capacity**

        Route capacity is estimated from observed service frequency
        and an assumed vehicle capacity of 14 seats per vehicle.

        **Segment classification**

        Estimated demand is compared with modeled capacity using the
        demand-to-capacity ratio:

        **D/C = estimated demand ÷ modeled capacity**

        Segments are then classified as overloaded, balanced or
        underused. Areas with estimated demand but no matched transit
        capacity are identified as potential coverage gaps.
        """
    )


with tab2:

    st.markdown("### Important limitations")

    st.markdown(
        """
        - The analysis estimates potential demand; it does not observe
          passenger boardings.

        - Matatu route data represents 2019–2020 service and may not
          reflect the current network.

        - Vehicle capacity is assumed rather than independently measured.

        - Coverage-gap results are sensitive to the number of candidate
          destinations considered during demand assignment.

        - Demand is assigned using all-or-nothing shortest-path routing,
          which can concentrate modeled flows onto fewer roads than
          real-world passengers would.

        - An OpenStreetMap network segment is a graph edge between
          intersections, not necessarily a full transit route or fixed
          distance.
        """
    )
