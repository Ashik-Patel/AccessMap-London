import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TfL Accessibility Gap Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
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
    .metric-lbl  { font-size: 0.78rem; color: #6c757d; margin: 0;
                   text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-sub  { font-size: 0.8rem; margin-top: 4px; color: #6c757d; }
    .section-hdr { font-size: 1rem; font-weight: 600; color: #1a1a2e;
                   padding-bottom: 0.4rem; border-bottom: 2px solid #e9ecef;
                   margin-bottom: 1rem; }
    .insight-box { background: #e8f5ee; border-left: 4px solid #1D9E75;
                   border-radius: 0 8px 8px 0; padding: 0.9rem 1.1rem;
                   margin: 0.8rem 0; font-size: 0.9rem; color: #0F6E56; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
COLOURS = {
    "Good (70-100)":   "#1D9E75",
    "Partial (40-69)": "#EF9F27",
    "Poor (0-39)":     "#E24B4A",
}
BAND_ORDER = ["Good (70-100)", "Partial (40-69)", "Poor (0-39)"]


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    master   = pd.read_csv("app/data/Station_Accessibility_Master.csv")
    lifts    = pd.read_csv("app/data/Lift_Details.csv")
    toilets  = pd.read_csv("app/data/Toilet_Details.csv")
    platform = pd.read_csv("app/data/Platform_Services_Detail.csv")

    master["AccessibilityBand"] = pd.Categorical(
        master["AccessibilityBand"], categories=BAND_ORDER, ordered=True
    )
    master["PrimaryZone"] = master["PrimaryZone"].astype(str)
    return master, lifts, toilets, platform


master, lifts, toilets, platform = load_data()


# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/TfL.svg/200px-TfL.svg.png",
        width=72,
    )
    st.title("TfL Accessibility")
    st.markdown("---")
    st.subheader("Filters")

    zones_all = sorted(z for z in master["PrimaryZone"].unique() if z != "Unknown")
    zones_sel = st.multiselect("Fare zone", zones_all, default=zones_all)

    bands_sel = st.multiselect("Accessibility band", BAND_ORDER, default=BAND_ORDER)

    wifi_sel  = st.selectbox("Wifi", ["All", "Yes", "No"])
    badge_sel = st.selectbox("Blue badge parking", ["All", "Yes", "No"])

    st.markdown("---")
    st.caption("Data: TfL Open Data · Built with Streamlit + Plotly")


# ── Apply filters ─────────────────────────────────────────────────────────────
df = master.copy()
if zones_sel:
    df = df[df["PrimaryZone"].isin(zones_sel)]
if bands_sel:
    df = df[df["AccessibilityBand"].isin(bands_sel)]
if wifi_sel != "All":
    df = df[df["Wifi"] == wifi_sel]
if badge_sel != "All":
    df = df[df["BlueBadgeCarParking"] == badge_sel]


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "Station map",
    "Lift coverage",
    "Toilets & facilities",
    "Station explorer",
])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## TfL Accessibility Gap Dashboard")
    st.caption(f"Showing **{len(df):,}** stations · filtered from {len(master):,} total")
    st.markdown("<br>", unsafe_allow_html=True)

    # KPI row
    lift_pct   = df["HasLift"].mean() * 100 if len(df) else 0
    toilet_pct = df["HasAccessibleToilet"].mean() * 100 if len(df) else 0
    avg_score  = df["AccessibilityScore"].mean() if len(df) else 0
    poor_n     = (df["AccessibilityBand"] == "Poor (0-39)").sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <p class="metric-lbl">Stations with a lift</p>
            <p class="metric-val">{lift_pct:.1f}%</p>
            <p class="metric-sub">{df['HasLift'].sum()} of {len(df)} stations</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card amber">
            <p class="metric-lbl">Accessible toilet coverage</p>
            <p class="metric-val">{toilet_pct:.1f}%</p>
            <p class="metric-sub">{df['HasAccessibleToilet'].sum()} of {len(df)} stations</p>
        </div>""", unsafe_allow_html=True)
    with c3:
        sc = "#1D9E75" if avg_score >= 70 else ("#EF9F27" if avg_score >= 40 else "#E24B4A")
        st.markdown(f"""<div class="metric-card blue">
            <p class="metric-lbl">Avg accessibility score</p>
            <p class="metric-val" style="color:{sc}">{avg_score:.1f}<span style="font-size:1rem;color:#aaa"> /100</span></p>
            <p class="metric-sub">Weighted across 5 factors</p>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card red">
            <p class="metric-lbl">Poor accessibility stations</p>
            <p class="metric-val" style="color:#E24B4A">{poor_n}</p>
            <p class="metric-sub">{poor_n/len(df)*100:.1f}% of filtered stations</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    # Donut — band distribution
    with col_l:
        st.markdown('<p class="section-hdr">Accessibility band distribution</p>',
                    unsafe_allow_html=True)
        band_df = (df["AccessibilityBand"].value_counts()
                     .reindex(BAND_ORDER).fillna(0).reset_index())
        band_df.columns = ["Band", "Count"]
        fig = px.pie(band_df, names="Band", values="Count",
                     color="Band", color_discrete_map=COLOURS, hole=0.55)
        fig.update_traces(textposition="outside", textinfo="percent+label")
        fig.update_layout(showlegend=False, height=300, margin=dict(t=10,b=10,l=10,r=10),
                          paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # Bar — avg score by zone
    with col_r:
        st.markdown('<p class="section-hdr">Average score by fare zone</p>',
                    unsafe_allow_html=True)
        zone_df = (df[df["PrimaryZone"] != "Unknown"]
                   .groupby("PrimaryZone")
                   .agg(AvgScore=("AccessibilityScore", "mean"),
                        Count=("Name", "count"))
                   .reset_index().sort_values("PrimaryZone"))
        zone_df["Colour"] = zone_df["AvgScore"].apply(
            lambda s: COLOURS["Good (70-100)"] if s >= 70
                      else (COLOURS["Partial (40-69)"] if s >= 40 else COLOURS["Poor (0-39)"])
        )
        fig = px.bar(zone_df, x="PrimaryZone", y="AvgScore",
                     color="Colour", color_discrete_map="identity",
                     text=zone_df["AvgScore"].round(1),
                     labels={"PrimaryZone": "Fare zone", "AvgScore": "Avg score"})
        fig.add_hline(y=40, line_dash="dot", line_color="#EF9F27",
                      annotation_text="Partial threshold (40)")
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, height=300, yaxis=dict(range=[0, 100]),
                          margin=dict(t=10,b=10,l=10,r=10),
                          paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # Insight box
    worst_z = zone_df.loc[zone_df["AvgScore"].idxmin(), "PrimaryZone"] if len(zone_df) else "N/A"
    st.markdown(f"""<div class="insight-box">
        <strong>Key insight:</strong> Only {lift_pct:.0f}% of TfL stations have step-free lift
        access. Accessible toilet coverage is even lower at {toilet_pct:.0f}%.
        Zone {worst_z} has the lowest average accessibility score in the current filter.
    </div>""", unsafe_allow_html=True)

    # Histogram
    st.markdown('<p class="section-hdr">Score distribution across all stations</p>',
                unsafe_allow_html=True)
    fig = px.histogram(df, x="AccessibilityScore", nbins=20,
                       color_discrete_sequence=["#378ADD"],
                       labels={"AccessibilityScore": "Accessibility score"})
    fig.add_vline(x=40, line_dash="dot", line_color="#EF9F27", annotation_text="Partial (40)")
    fig.add_vline(x=70, line_dash="dot", line_color="#1D9E75", annotation_text="Good (70)")
    fig.update_layout(height=260, margin=dict(t=10,b=10,l=10,r=10),
                      paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — MAP
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## Station accessibility map")
    st.caption("Bubble size = lift count · Colour = accessibility band · Hover for details")

    map_df = df.dropna(subset=["Lat", "Lon"]).copy()
    map_df["BubbleSize"] = (map_df["TotalLifts"] + 1) * 4

    fig = px.scatter_mapbox(
        map_df, lat="Lat", lon="Lon",
        color="AccessibilityBand", color_discrete_map=COLOURS,
        size="BubbleSize", size_max=18,
        hover_name="Name",
        hover_data={
            "AccessibilityScore": True, "TotalLifts": True,
            "AccessibleToilets": True, "FareZones": True,
            "LinesServed": True, "BubbleSize": False,
            "Lat": False, "Lon": False,
        },
        zoom=10, center={"lat": 51.5098, "lon": -0.1181},
        mapbox_style="carto-positron",
        category_orders={"AccessibilityBand": BAND_ORDER},
        height=580,
    )
    fig.update_layout(
        margin=dict(t=0,b=0,l=0,r=0),
        legend=dict(title="Band", orientation="v", x=0.01, y=0.99,
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="#dee2e6", borderwidth=1),
    )
    st.plotly_chart(fig, use_container_width=True)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Good stations on map",
                  map_df[map_df["AccessibilityBand"] == "Good (70-100)"].shape[0])
    with m2:
        st.metric("Avg lifts — Good band",
                  f"{map_df[map_df['AccessibilityBand']=='Good (70-100)']['TotalLifts'].mean():.1f}")
    with m3:
        st.metric("Avg lifts — Poor band",
                  f"{map_df[map_df['AccessibilityBand']=='Poor (0-39)']['TotalLifts'].mean():.1f}")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — LIFT COVERAGE
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## Lift coverage analysis")

    lc1, lc2, lc3, lc4 = st.columns(4)
    with lc1:
        st.metric("Stations with lifts",
                  f"{df['HasLift'].sum()} ({df['HasLift'].mean()*100:.0f}%)")
    with lc2:
        st.metric("Total lifts in network", int(df["TotalLifts"].sum()))
    with lc3:
        st.metric("Limited capacity lifts", int(df["LimitedCapacityLifts"].sum()))
    with lc4:
        st.metric("Max lifts at one station", int(df["TotalLifts"].max()))

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<p class="section-hdr">Lift coverage by fare zone</p>',
                    unsafe_allow_html=True)
        zl = (df[df["PrimaryZone"] != "Unknown"]
              .groupby("PrimaryZone")
              .agg(WithLift=("HasLift", "sum"), Total=("HasLift", "count"))
              .reset_index())
        zl["NoLift"] = zl["Total"] - zl["WithLift"]

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Has lift", x=zl["PrimaryZone"],
                             y=zl["WithLift"], marker_color="#1D9E75"))
        fig.add_trace(go.Bar(name="No lift",  x=zl["PrimaryZone"],
                             y=zl["NoLift"],  marker_color="#E24B4A", opacity=0.75))
        fig.update_layout(barmode="stack", height=320, xaxis_title="Fare zone",
                          yaxis_title="Stations", margin=dict(t=10,b=10,l=10,r=10),
                          paper_bgcolor="rgba(0,0,0,0)",
                          legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown('<p class="section-hdr">Top 15 stations by lift count</p>',
                    unsafe_allow_html=True)
        top = (df[df["TotalLifts"] > 0]
               .nlargest(15, "TotalLifts")
               [["Name", "TotalLifts", "AccessibilityBand"]]
               .sort_values("TotalLifts"))
        fig = px.bar(top, x="TotalLifts", y="Name", orientation="h",
                     color="AccessibilityBand", color_discrete_map=COLOURS,
                     labels={"TotalLifts": "Number of lifts", "Name": ""},
                     category_orders={"AccessibilityBand": BAND_ORDER})
        fig.update_layout(showlegend=False, height=360,
                          margin=dict(t=10,b=10,l=10,r=10),
                          paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<p class="section-hdr">Stations with no lift — gap list</p>',
                unsafe_allow_html=True)
    no_lift = (df[df["HasLift"] == 0]
               [["Name", "FareZones", "LinesServed", "AccessibilityScore", "AccessibilityBand"]]
               .sort_values("AccessibilityScore")
               .rename(columns={"Name":"Station","FareZones":"Zones",
                                "LinesServed":"Lines","AccessibilityScore":"Score",
                                "AccessibilityBand":"Band"}))
    st.dataframe(no_lift, height=340, use_container_width=True)
    st.caption(f"{len(no_lift)} stations have no lift")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — TOILETS & FACILITIES
# ═════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## Toilets & facilities analysis")

    tf1, tf2, tf3, tf4 = st.columns(4)
    with tf1:
        st.metric("Stations with any toilet", (df["TotalToilets"] > 0).sum())
    with tf2:
        st.metric("Accessible toilet stations",
                  df["HasAccessibleToilet"].sum(),
                  delta=f"{df['HasAccessibleToilet'].mean()*100:.0f}% coverage")
    with tf3:
        st.metric("Baby changing available", int(df["HasBabyChanging"].sum()))
    with tf4:
        st.metric("Stations with free toilets", (df["FreeToilets"] > 0).sum())

    col_f1, col_f2 = st.columns(2)

    with col_f1:
        st.markdown('<p class="section-hdr">Accessible toilet coverage by zone</p>',
                    unsafe_allow_html=True)
        zt = (df[df["PrimaryZone"] != "Unknown"]
              .groupby("PrimaryZone")
              .agg(WithToilet=("HasAccessibleToilet", "sum"),
                   Total=("Name", "count"))
              .reset_index())
        zt["Pct"] = (zt["WithToilet"] / zt["Total"] * 100).round(1)

        fig = px.bar(zt, x="PrimaryZone", y="Pct",
                     color="Pct",
                     color_continuous_scale=[[0,"#E24B4A"],[0.4,"#EF9F27"],[0.7,"#1D9E75"]],
                     text=zt["Pct"].astype(str) + "%",
                     labels={"PrimaryZone": "Fare zone", "Pct": "% with accessible toilet"})
        fig.update_traces(textposition="outside")
        fig.update_layout(height=300, yaxis=dict(range=[0, 100]),
                          coloraxis_showscale=False,
                          margin=dict(t=10,b=10,l=10,r=10),
                          paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col_f2:
        st.markdown('<p class="section-hdr">Facility availability across network</p>',
                    unsafe_allow_html=True)
        fac = {
            "Lift":               df["HasLift"].sum(),
            "Accessible toilet":  df["HasAccessibleToilet"].sum(),
            "Baby changing":      int(df["HasBabyChanging"].sum()),
            "Free toilet":        (df["FreeToilets"] > 0).sum(),
            "Wifi":               (df["Wifi"] == "Yes").sum(),
            "Blue badge parking": (df["BlueBadgeCarParking"] == "Yes").sum(),
            "Bus interchange":    (df["MainBusInterchange"] == "Yes").sum(),
            "Rail interchange":   (df["NationalRailInterchange"] == "Yes").sum(),
        }
        fac_df = pd.DataFrame(fac.items(), columns=["Facility", "Stations"])
        fac_df["Pct"] = (fac_df["Stations"] / len(df) * 100).round(1)
        fac_df = fac_df.sort_values("Stations")

        fig = px.bar(fac_df, x="Stations", y="Facility", orientation="h",
                     text=fac_df["Pct"].astype(str) + "%",
                     color="Stations",
                     color_continuous_scale=[[0,"#E24B4A"],[0.5,"#EF9F27"],[1,"#1D9E75"]])
        fig.update_traces(textposition="outside")
        fig.update_layout(height=340, coloraxis_showscale=False,
                          margin=dict(t=10,b=10,l=10,r=10),
                          paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<p class="section-hdr">Accessibility score vs toilet provision</p>',
                unsafe_allow_html=True)
    fig = px.scatter(df, x="AccessibilityScore", y="TotalToilets",
                     color="AccessibilityBand", color_discrete_map=COLOURS,
                     hover_name="Name",
                     hover_data={"FareZones": True, "AccessibleToilets": True},
                     labels={"AccessibilityScore": "Accessibility score",
                             "TotalToilets": "Total toilets at station"},
                     category_orders={"AccessibilityBand": BAND_ORDER},
                     opacity=0.7)
    fig.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10),
                      paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 5 — STATION EXPLORER
# ═════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("## Station explorer")

    search = st.text_input("Search station name",
                           placeholder="e.g. King's Cross, Stratford, Paddington...")
    results = df[df["Name"].str.contains(search, case=False, na=False)] if search else df.copy()

    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        sort_col = st.selectbox("Sort by",
                                ["AccessibilityScore", "TotalLifts", "AccessibleToilets", "Name"])
    with col_s2:
        asc = st.checkbox("Ascending", value=(sort_col == "Name"))

    show = (results[["Name", "FareZones", "LinesServed", "AccessibilityScore",
                      "AccessibilityBand", "TotalLifts", "AccessibleToilets",
                      "HasRamp", "Wifi", "BlueBadgeCarParking"]]
            .sort_values(sort_col, ascending=asc)
            .reset_index(drop=True))
    show.columns = ["Station", "Zones", "Lines", "Score", "Band",
                    "Lifts", "Acc. Toilets", "Ramp", "Wifi", "Blue Badge"]

    st.dataframe(show, height=380, use_container_width=True)
    st.caption(f"{len(show)} stations")

    # ── Individual station scorecard ──────────────────────────────
    st.markdown("---")
    st.markdown('<p class="section-hdr">Individual station scorecard</p>',
                unsafe_allow_html=True)

    names = results["Name"].sort_values().tolist()
    if names:
        picked = st.selectbox("Select a station", names)
        row = df[df["Name"] == picked].iloc[0]
        bc  = COLOURS.get(row["AccessibilityBand"], "#378ADD")

        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.markdown(f"""<div class="metric-card" style="border-left-color:{bc}">
                <p class="metric-lbl">Accessibility score</p>
                <p class="metric-val" style="color:{bc}">{row['AccessibilityScore']:.0f}
                    <span style="font-size:1rem;color:#aaa">/100</span></p>
                <p class="metric-sub">{row['AccessibilityBand']}</p>
            </div>""", unsafe_allow_html=True)
        with sc2:
            st.markdown(f"""<div class="metric-card amber">
                <p class="metric-lbl">Total lifts</p>
                <p class="metric-val">{int(row['TotalLifts'])}</p>
                <p class="metric-sub">{int(row['LimitedCapacityLifts'])} limited capacity</p>
            </div>""", unsafe_allow_html=True)
        with sc3:
            st.markdown(f"""<div class="metric-card blue">
                <p class="metric-lbl">Accessible toilets</p>
                <p class="metric-val">{int(row['AccessibleToilets'])}</p>
                <p class="metric-sub">{int(row['TotalToilets'])} total toilets on site</p>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        d1, d2 = st.columns(2)

        with d1:
            st.markdown("**Station details**")
            st.write(f"Fare zones: {row['FareZones']}")
            st.write(f"Lines: {row['LinesServed'] if pd.notna(row.get('LinesServed')) else 'N/A'}")
            st.write(f"Wifi: {row['Wifi']}")
            st.write(f"Blue badge parking: {row['BlueBadgeCarParking']}")
            st.write(f"Bus interchange: {row['MainBusInterchange']}")
            st.write(f"National Rail: {row['NationalRailInterchange']}")

        with d2:
            st.markdown("**Score breakdown**")
            factors = pd.DataFrame([
                {"Factor": "Lift (30 pts)",              "Earned": 30 if row["HasLift"] else 0,             "Max": 30},
                {"Factor": "Step-free platforms (25 pts)","Earned": round(row["StepFreePlatformPct"]*25,1), "Max": 25},
                {"Factor": "Accessible toilet (20 pts)", "Earned": 20 if row["HasAccessibleToilet"] else 0, "Max": 20},
                {"Factor": "Level access (15 pts)",      "Earned": round(row["LevelAccessPct"]*15,1),       "Max": 15},
                {"Factor": "Ramp route (10 pts)",        "Earned": 10 if row["HasRamp"] else 0,             "Max": 10},
            ])
            fig = px.bar(factors, x="Earned", y="Factor", orientation="h",
                         color="Earned",
                         color_continuous_scale=[[0,"#E24B4A"],[0.5,"#EF9F27"],[1,"#1D9E75"]],
                         range_x=[0, 30], text="Earned")
            fig.update_traces(textposition="outside")
            fig.update_layout(height=240, coloraxis_showscale=False, showlegend=False,
                              margin=dict(t=10,b=10,l=10,r=10),
                              paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No stations match your search.")
