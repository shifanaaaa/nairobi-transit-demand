import streamlit as st
from streamlit_folium import st_folium
import folium
import json

# ---------------------------------------------------------
# PAGE CONFIG
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

    /* Overall page */
    .block-container {
        max-width: 1500px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }

    /* Main title */
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

    /* Section headings */
    .section-title {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b7280;
        margin-top: 1.4rem;
        margin-bottom: 0.6rem;
    }

    /* Small metadata text */
    .meta {
        font-size: 0.82rem;
        color: #6b7280;
    }

    /* Metric labels */
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem;
        color: #6b7280;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.55rem;
        font-weight: 600;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        border-right: 1px solid #e5e7eb;
    }

    /* Hide Streamlit branding */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

</style>
""", unsafe_allow_html=True)


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

with open(filename) as f:
    data = json.load(f)


# ---------------------------------------------------------
# COUNTS
# ---------------------------------------------------------

counts = {}

for row in data:
    flag = row["flag"]
    counts[flag] = counts.get(flag, 0) + 1


total = len(data)


# ---------------------------------------------------------
# NETWORK SUMMARY
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">Network overview</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1.15])

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

colors = {
    "underused": "#377eb8",
    "balanced": "#4daf4a",
    "overloaded": "#d73027",
    "coverage_gap": "#fdae61"
}

enabled = {
    "underused": show_underused,
    "balanced": show_balanced,
    "overloaded": show_overloaded,
    "coverage_gap": show_gaps
}

m = folium.Map(
    location=[-1.286389, 36.817223],
    zoom_start=12,
    tiles="OpenStreetMap",
    control_scale=True
)


for row in data:

    flag = row["flag"]

    # Network visibility
    if not show_network and flag not in ("overloaded", "coverage_gap"):
        continue

    # Classification visibility
    if flag in enabled and not enabled[flag]:
        continue

    dc_ratio = row.get("dc_ratio")

    if dc_ratio is not None:
        dc_text = f"{dc_ratio:.2f}×"
    else:
        dc_text = "N/A"

    demand = row.get(
        "estimated_demand_per_hour",
        0
    )

    capacity = row.get(
        "capacity_per_hour",
        0
    )

    label = flag.replace("_", " ").title()

    tooltip = f"""
    <div style="font-family: Arial; font-size: 13px; line-height: 1.5;">
        <b>{label}</b><br>
        Demand: {demand:.0f} passenger-trips/hr<br>
        Capacity: {capacity:.0f} passenger-spaces/hr<br>
        D/C ratio: {dc_text}
    </div>
    """

    folium.PolyLine(
        locations=row["coords"],
        color=colors.get(flag, "#888888"),
        weight=6 if flag in ("overloaded", "coverage_gap") else 2.5,
        opacity=0.85 if flag in ("overloaded", "coverage_gap") else 0.55,
        tooltip=folium.Tooltip(tooltip)
    ).add_to(m)


st_folium(
    m,
    width=None,
    height=680
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