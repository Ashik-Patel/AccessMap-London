import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TfL Accessibility Gap Dashboard",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
        border-left: 4px solid #1D9E75;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .metric-card.amber { border-left-color: #EF9F27; }
    .metric-card.red   { border-left-color: #E24B4A; }
    .metric-card.blue  { border-left-color: #378ADD; }
    .metric-val  { font-size: 2rem; font-weight: 700; color: #1a1a2e; margin: 0; }
    .metric-lbl  { font-size: 0.8rem; color: #6c757d; margin: 0; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-delta { font-size: 0.8rem; margin-top: 4px; }
    .section-header {
        font-size: 1.1rem; font-weight: 600; color: #1a1a2e;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e9ecef;
        margin-bottom: 1rem;
    }
    .insight-box {
        background: #e8f5ee;
        border-left: 4px solid #1D9E75;
        border-radius: 0 8px 8px 0;
        padding: 0.9rem 1.1rem;
        margin: 0.8rem 0;
        font-size: 0.9rem;
        color: #0F6E56;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ── Colour constants ──────────────────────────────────────────────────────────
COLOURS = {
    "Good (70-100)":    "#1D9E75",
    "Partial (40-69)":  "#EF9F27",
    "Poor (0-39)":      "#E24B4A",
}
BAND_ORDER = ["Good (70-100)", "Partial (40-69)", "Poor (0-39)"]

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    master = pd.read_csv("data/Station_Accessibility_Master.csv")
    lifts  = pd.read_csv("data/Lift_Details.csv")
    toilets = pd.read_csv("data/Toilet_Details.csv")
    platforms = pd.read_csv("data/Platform_Services_Detail.csv")

    master["AccessibilityBand"] = pd.Categorical(
        master["AccessibilityBand"], categories=BAND_ORDER, ordered=True
    )
    master["PrimaryZone"] = master["PrimaryZone"].astype(str)
    return master, lifts, toilets, platforms

master, lifts, toilets, platforms = load_data()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/TfL.svg/200px-TfL.svg.png", width=80)
    st.title("TfL Accessibility")
    st.markdown("---")
    st.subheader("Filters")

    zones_available = sorted([z for z in master["PrimaryZone"].unique() if z != "Unknown"])
    zones_selected = st.multiselect(
        "Fare zone", zones_available, default=zones_available, help="Filter by TfL fare zone"
    )

    bands_selected = st.multiselect(
        "Accessibility band", BAND_ORDER, default=BAND_ORDER
    )

    wifi_filter = st.selectbox("Wifi", ["All", "Yes", "No"])
    blue_badge_filter = st.selectbox("Blue badge parking", ["All", "Yes", "No"])

    st.markdown("---")
    st.caption("Data: TfL Open Data · Built with Streamlit")

# ── Apply filters ─────────────────────────────────────────────────────────────
df = master.copy()
if zones_selected:
    df = df[df["PrimaryZone"].isin(zones_selected)]
if bands_selected:
    df = df[df["AccessibilityBand"].isin(bands_selected)]
if wifi_filter != "All":
    df = df[df["Wifi"] == wifi_filter]
if blue_badge_filter != "All":
    df = df[df["BlueBadgeCarParking"] == blue_badge_filter]

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🗺️ Station Map",
    "🛗 Lift Coverage",
    "🚻 Toilets & Facilities",
    "🔍 Station Explorer",
])

# ═══════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## TfL Accessibility Gap Dashboard")
    st.markdown(f"Analysing **{len(df):,}** stations · Filtered from {len(master):,} total")

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    lift_pct  = (df["HasLift"].sum() / len(df) * 100) if len(df) else 0
    toilet_pct = (df["HasAccessibleToilet"].sum() / len(df) * 100) if len(df) else 0
    avg_score  = df["AccessibilityScore"].mean() if len(df) else 0
    poor_count = (df["AccessibilityBand"] == "Poor (0-39)").sum()

    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-lbl">Stations with a lift</p>
            <p class="metric-val">{lift_pct:.1f}%</p>
            <p class="metric-delta" style="color:#E24B4A">{df['HasLift'].sum()} of {len(df)} stations</p>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-card amber">
            <p class="metric-lbl">Accessible toilet coverage</p>
            <p class="metric-val">{toilet_pct:.1f}%</p>
            <p class="metric-delta" style="color:#E24B4A">{df['HasAccessibleToilet'].sum()} of {len(df)} stations</p>
        </div>""", unsafe_allow_html=True)

    with c3:
        score_color = "#1D9E75" if avg_score >= 70 else ("#EF9F27" if avg_score >= 40 else "#E24B4A")
        st.markdown(f"""
        <div class="metric-card blue">
            <p class="metric-lbl">Avg accessibility score</p>
            <p class="metric-val" style="color:{score_color}">{avg_score:.1f}<span style="font-size:1rem;color:#aaa"> /100</span></p>
            <p class="metric-delta" style="color:#6c757d">Weighted across 5 factors</p>
        </div>""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card red">
            <p class="metric-lbl">Poor accessibility stations</p>
            <p class="metric-val" style="color:#E24B4A">{poor_count}</p>
            <p class="metric-delta" style="color:#E24B4A">{poor_count/len(df)*100:.1f}% of filtered stations</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown('<p class="section-header">Accessibility band distribution</p>', unsafe_allow_html=True)
        band_counts = df["AccessibilityBand"].value_counts().reindex(BAND_ORDER).fillna(0).reset_index()
        band_counts.columns = ["Band", "Count"]
        fig_donut = px.pie(
            band_counts, names="Band", values="Count",
            color="Band", color_discrete_map=COLOURS,
            hole=0.55,
        )
        fig_donut.update_traces(textposition="outside", textinfo="percent+label")
        fig_donut.update_layout(
            showlegend=False, margin=dict(t=10, b=10, l=10, r=10),
            height=300, paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_right:
        st.markdown('<p class="section-header">Average score by fare zone</p>', unsafe_allow_html=True)
        zone_df = df[df["PrimaryZone"] != "Unknown"].groupby("PrimaryZone").agg(
            AvgScore=("AccessibilityScore", "mean"),
            Count=("Name", "count"),
        ).reset_index().sort_values("PrimaryZone")
        zone_df["Colour"] = zone_df["AvgScore"].apply(
            lambda s: COLOURS["Good (70-100)"] if s >= 70 else (COLOURS["Partial (40-69)"] if s >= 40 else COLOURS["Poor (0-39)"])
        )
        fig_zone = px.bar(
            zone_df, x="PrimaryZone", y="AvgScore",
            color="Colour", color_discrete_map="identity",
            labels={"PrimaryZone": "Fare Zone", "AvgScore": "Avg Score"},
            text=zone_df["AvgScore"].round(1),
        )
        fig_zone.add_hline(y=40, line_dash="dot", line_color="#EF9F27",
                           annotation_text="Partial threshold (40)", annotation_position="top right")
        fig_zone.update_traces(textposition="outside")
        fig_zone.update_layout(
            showlegend=False, margin=dict(t=10, b=10, l=10, r=10),
            height=300, paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(range=[0, 100]),
        )
        st.plotly_chart(fig_zone, use_container_width=True)

    # Insight box
    worst_zone = zone_df.loc[zone_df["AvgScore"].idxmin(), "PrimaryZone"] if len(zone_df) else "N/A"
    st.markdown(f"""
    <div class="insight-box">
        <strong>Key insight:</strong> Only {lift_pct:.0f}% of TfL stations have step-free lift access.
        Accessible toilet coverage is even lower at {toilet_pct:.0f}%.
        Zone {worst_zone} has the lowest average accessibility score among filtered stations.
    </div>""", unsafe_allow_html=True)

    # Score distribution histogram
    st.markdown('<p class="section-header">Accessibility score distribution</p>', unsafe_allow_html=True)
    fig_hist = px.histogram(
        df, x="AccessibilityScore", nbins=20,
        color_discrete_sequence=["#378ADD"],
        labels={"AccessibilityScore": "Accessibility Score", "count": "Number of Stations"},
    )
    fig_hist.add_vline(x=40, line_dash="dot", line_color="#EF9F27", annotation_text="Partial (40)")
    fig_hist.add_vline(x=70, line_dash="dot", line_color="#1D9E75", annotation_text="Good (70)")
    fig_hist.update_layout(
        margin=dict(t=10, b=10, l=10, r=10), height=260,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_hist, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 2 — MAP
# ═══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## Station Accessibility Map")
    st.caption("Bubble size = number of lifts · Colour = accessibility band · Click a station for details")

    map_df = df.dropna(subset=["Lat", "Lon"]).copy()
    map_df["BubbleSize"] = (map_df["TotalLifts"] + 1) * 4

    fig_map = px.scatter_mapbox(
        map_df,
        lat="Lat", lon="Lon",
        color="AccessibilityBand",
        color_discrete_map=COLOURS,
        size="BubbleSize",
        size_max=18,
        hover_name="Name",
        hover_data={
            "AccessibilityScore": True,
            "TotalLifts": True,
            "AccessibleToilets": True,
            "FareZones": True,
            "LinesServed": True,
            "BubbleSize": False,
            "Lat": False,
            "Lon": False,
        },
        zoom=10,
        center={"lat": 51.509865, "lon": -0.118092},
        mapbox_style="carto-positron",
        category_orders={"AccessibilityBand": BAND_ORDER},
        height=600,
    )
    fig_map.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        legend=dict(title="Accessibility band", orientation="v",
                    x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="#dee2e6", borderwidth=1),
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # Quick map stats
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        good_stations = map_df[map_df["AccessibilityBand"] == "Good (70-100)"]["Name"].tolist()
        st.metric("Good stations on map", len(good_stations))
    with mc2:
        good_avg = map_df[map_df['AccessibilityBand']=='Good (70-100)']['TotalLifts'].mean()
        st.metric("Avg lifts (Good band)", f"{good_avg:.1f}" if pd.notna(good_avg) else "N/A")
    with mc3:
        poor_avg = map_df[map_df['AccessibilityBand']=='Poor (0-39)']['TotalLifts'].mean()
        st.metric("Avg lifts (Poor band)", f"{poor_avg:.1f}" if pd.notna(poor_avg) else "N/A")


# ═══════════════════════════════════════════════════════════════════
# TAB 3 — LIFT COVERAGE
# ═══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## Lift Coverage Analysis")

    lc1, lc2, lc3, lc4 = st.columns(4)
    if len(df) == 0:
        for col in [lc1, lc2, lc3, lc4]:
            with col:
                st.warning("No stations match the current filters.")
    else:
        with lc1:
            lift_mean = df['HasLift'].mean() * 100
            st.metric("Stations with lifts", f"{df['HasLift'].sum()} ({lift_mean:.0f}%)")
        with lc2:
            st.metric("Total lifts", int(df["TotalLifts"].sum()))
        with lc3:
            st.metric("Limited capacity lifts", int(df["LimitedCapacityLifts"].sum()))
        with lc4:
            st.metric("Max lifts at one station", int(df["TotalLifts"].max()))

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<p class="section-header">Lift coverage by fare zone</p>', unsafe_allow_html=True)
        zone_lift = df[df["PrimaryZone"] != "Unknown"].groupby("PrimaryZone").agg(
            WithLift=("HasLift", "sum"),
            Total=("HasLift", "count"),
        ).reset_index()
        zone_lift["WithoutLift"] = zone_lift["Total"] - zone_lift["WithLift"]
        zone_lift["PctWithLift"] = (zone_lift["WithLift"] / zone_lift["Total"] * 100).round(1)

        fig_lift_zone = go.Figure()
        fig_lift_zone.add_trace(go.Bar(
            name="Has lift", x=zone_lift["PrimaryZone"], y=zone_lift["WithLift"],
            marker_color="#1D9E75",
        ))
        fig_lift_zone.add_trace(go.Bar(
            name="No lift", x=zone_lift["PrimaryZone"], y=zone_lift["WithoutLift"],
            marker_color="#E24B4A",
        ))
        fig_lift_zone.update_layout(
            barmode="stack", height=320,
            xaxis_title="Fare Zone", yaxis_title="Stations",
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.1),
        )
        st.plotly_chart(fig_lift_zone, use_container_width=True)

    with col_b:
        st.markdown('<p class="section-header">Top 15 stations by lift count</p>', unsafe_allow_html=True)
        top_lift = df[df["TotalLifts"] > 0].nlargest(15, "TotalLifts")[["Name", "TotalLifts", "FareZones", "AccessibilityBand"]]
        fig_top_lift = px.bar(
            top_lift.sort_values("TotalLifts"), x="TotalLifts", y="Name",
            color="AccessibilityBand", color_discrete_map=COLOURS,
            orientation="h",
            labels={"TotalLifts": "Number of lifts", "Name": ""},
            category_orders={"AccessibilityBand": BAND_ORDER},
        )
        fig_top_lift.update_layout(
            height=360, margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
        )
        st.plotly_chart(fig_top_lift, use_container_width=True)

    # Stations with NO lift — table
    st.markdown('<p class="section-header">Stations with no lift — potential gap list</p>', unsafe_allow_html=True)
    no_lift = df[df["HasLift"] == 0][["Name", "FareZones", "LinesServed", "AccessibilityScore", "AccessibilityBand"]].sort_values("AccessibilityScore")
    no_lift.columns = ["Station", "Zones", "Lines", "Score", "Band"]
    st.dataframe(
        no_lift.style.apply(
            lambda row: ["background-color: #ffeaea"] * len(row) if row["Band"] == "Poor (0-39)"
            else ["background-color: #fff8e6"] * len(row), axis=1
        ),
        height=350, use_container_width=True,
    )
    st.caption(f"{len(no_lift)} stations have no lift · Red = Poor band")


# ═══════════════════════════════════════════════════════════════════
# TAB 4 — TOILETS & FACILITIES
# ═══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## Toilets & Facilities Analysis")

    tf1, tf2, tf3, tf4 = st.columns(4)
    if len(df) == 0:
        for col in [tf1, tf2, tf3, tf4]:
            with col:
                st.warning("No stations match the current filters.")
    else:
        with tf1:
            st.metric("Stations with any toilet", (df["TotalToilets"] > 0).sum())
        with tf2:
            toilet_pct = df['HasAccessibleToilet'].mean() * 100
            st.metric("Accessible toilets (stations)", df["HasAccessibleToilet"].sum(),
                      delta=f"{toilet_pct:.0f}% coverage")
        with tf3:
            st.metric("Stations with baby changing", int(df["HasBabyChanging"].sum()))
        with tf4:
            st.metric("Stations with free toilets", (df["FreeToilets"] > 0).sum())

    col_f1, col_f2 = st.columns(2)

    with col_f1:
        st.markdown('<p class="section-header">Accessible toilet coverage by zone</p>', unsafe_allow_html=True)
        zone_toilet = df[df["PrimaryZone"] != "Unknown"].groupby("PrimaryZone").agg(
            WithAccessible=("HasAccessibleToilet", "sum"),
            Total=("Name", "count"),
        ).reset_index()
        zone_toilet["Pct"] = (zone_toilet["WithAccessible"] / zone_toilet["Total"] * 100).round(1)

        fig_toilet = px.bar(
            zone_toilet, x="PrimaryZone", y="Pct",
            color="Pct",
            color_continuous_scale=[[0, "#E24B4A"], [0.4, "#EF9F27"], [0.7, "#1D9E75"]],
            labels={"PrimaryZone": "Fare Zone", "Pct": "% with accessible toilet"},
            text=zone_toilet["Pct"].astype(str) + "%",
        )
        fig_toilet.update_traces(textposition="outside")
        fig_toilet.update_layout(
            height=300, margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False,
            yaxis=dict(range=[0, 100]),
        )
        st.plotly_chart(fig_toilet, use_container_width=True)

    with col_f2:
        st.markdown('<p class="section-header">Facility availability breakdown</p>', unsafe_allow_html=True)
        facilities = {
            "Lift":              df["HasLift"].sum(),
            "Accessible toilet": df["HasAccessibleToilet"].sum(),
            "Baby changing":     df["HasBabyChanging"].sum(),
            "Free toilet":       (df["FreeToilets"] > 0).sum(),
            "Wifi":              (df["Wifi"] == "Yes").sum(),
            "Blue badge parking":(df["BlueBadgeCarParking"] == "Yes").sum(),
            "Bus interchange":   (df["MainBusInterchange"] == "Yes").sum(),
            "Rail interchange":  (df["NationalRailInterchange"] == "Yes").sum(),
        }
        fac_df = pd.DataFrame(list(facilities.items()), columns=["Facility", "Stations"])
        fac_df["Pct"] = (fac_df["Stations"] / len(df) * 100).round(1)
        fac_df = fac_df.sort_values("Stations")

        fig_fac = px.bar(
            fac_df, x="Stations", y="Facility", orientation="h",
            text=fac_df["Pct"].astype(str) + "%",
            color="Stations",
            color_continuous_scale=[[0, "#E24B4A"], [0.5, "#EF9F27"], [1, "#1D9E75"]],
        )
        fig_fac.update_traces(textposition="outside")
        fig_fac.update_layout(
            height=340, margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False,
        )
        st.plotly_chart(fig_fac, use_container_width=True)

    # Accessibility vs toilets scatter
    st.markdown('<p class="section-header">Accessibility score vs toilet provision</p>', unsafe_allow_html=True)
    fig_scatter = px.scatter(
        df, x="AccessibilityScore", y="TotalToilets",
        color="AccessibilityBand",
        color_discrete_map=COLOURS,
        hover_name="Name",
        hover_data={"FareZones": True, "AccessibleToilets": True},
        labels={"AccessibilityScore": "Accessibility Score", "TotalToilets": "Total Toilets at Station"},
        category_orders={"AccessibilityBand": BAND_ORDER},
        opacity=0.7,
    )
    fig_scatter.update_layout(
        height=320, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 5 — STATION EXPLORER
# ═══════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("## Station Explorer")
    st.caption("Search and compare individual stations")

    search = st.text_input("Search station name", placeholder="e.g. King's Cross, Stratford...")

    if search:
        results = df[df["Name"].str.contains(search, case=False, na=False)]
    else:
        results = df.copy()

    sort_col = st.selectbox("Sort by", ["AccessibilityScore", "TotalLifts", "AccessibleToilets", "Name"],
                            index=0)
    sort_asc = st.checkbox("Ascending", value=True if sort_col == "Name" else False)

    display_cols = ["Name", "FareZones", "LinesServed", "AccessibilityScore", "AccessibilityBand",
                    "TotalLifts", "AccessibleToilets", "HasRamp", "Wifi", "BlueBadgeCarParking"]
    display_df = results[display_cols].sort_values(sort_col, ascending=sort_asc).reset_index(drop=True)
    display_df.columns = ["Station", "Zones", "Lines", "Score", "Band",
                           "Lifts", "Acc. Toilets", "Has Ramp", "Wifi", "Blue Badge"]

    st.dataframe(display_df, height=400, use_container_width=True)
    st.caption(f"Showing {len(display_df)} stations")

    # Detailed scorecard
    st.markdown("---")
    st.markdown('<p class="section-header">Station scorecard</p>', unsafe_allow_html=True)
    station_names = results["Name"].sort_values().tolist()
    if station_names:
        selected_station = st.selectbox("Select a station for full detail", station_names)
        row = df[df["Name"] == selected_station].iloc[0]

        band_colour = COLOURS.get(row["AccessibilityBand"], "#378ADD")

        sc1, sc2, sc3 = st.columns([1, 1, 1])
        with sc1:
            st.markdown(f"""
            <div class="metric-card" style="border-left-color:{band_colour}">
                <p class="metric-lbl">Accessibility score</p>
                <p class="metric-val" style="color:{band_colour}">{row['AccessibilityScore']:.0f}<span style="font-size:1rem;color:#aaa">/100</span></p>
                <p class="metric-delta">{row['AccessibilityBand']}</p>
            </div>""", unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""
            <div class="metric-card amber">
                <p class="metric-lbl">Total lifts</p>
                <p class="metric-val">{int(row['TotalLifts'])}</p>
                <p class="metric-delta">{int(row['LimitedCapacityLifts'])} limited capacity</p>
            </div>""", unsafe_allow_html=True)
        with sc3:
            st.markdown(f"""
            <div class="metric-card blue">
                <p class="metric-lbl">Accessible toilets</p>
                <p class="metric-val">{int(row['AccessibleToilets'])}</p>
                <p class="metric-delta">{int(row['TotalToilets'])} total toilets</p>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            st.markdown("**Station details**")
            st.write(f"📍 Fare zones: {row['FareZones']}")
            st.write(f"🚇 Lines served: {row['LinesServed'] if pd.notna(row['LinesServed']) else 'N/A'}")
            st.write(f"📶 Wifi: {row['Wifi']}")
            st.write(f"🅿️ Blue badge parking: {row['BlueBadgeCarParking']}")
            st.write(f"🚌 Bus interchange: {row['MainBusInterchange']}")
            st.write(f"🚂 National Rail interchange: {row['NationalRailInterchange']}")

        with detail_col2:
            st.markdown("**Accessibility breakdown**")
            factors = {
                "Has lift (30pts)":           30 if row["HasLift"] else 0,
                "Step-free platforms (25pts)": round(row["StepFreePlatformPct"] * 25, 1),
                "Accessible toilet (20pts)":   20 if row["HasAccessibleToilet"] else 0,
                "Level access (15pts)":        round(row["LevelAccessPct"] * 15, 1),
                "Ramp route (10pts)":          10 if row["HasRamp"] else 0,
            }
            score_df = pd.DataFrame(list(factors.items()), columns=["Factor", "Points Earned"])
            fig_score = px.bar(
                score_df, x="Points Earned", y="Factor", orientation="h",
                color="Points Earned",
                color_continuous_scale=[[0, "#E24B4A"], [0.5, "#EF9F27"], [1, "#1D9E75"]],
                range_x=[0, 30],
                text="Points Earned",
            )
            fig_score.update_traces(textposition="outside")
            fig_score.update_layout(
                height=240, margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False,
                showlegend=False,
            )
            st.plotly_chart(fig_score, use_container_width=True)
    else:
        st.info("No stations match your search.")