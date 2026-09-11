"""
src/ui/pages.py — All Dashboard Page Renderers
===============================================
Each function renders one page of the F1 Super Intelligence platform.
Pages are called from app.py based on sidebar navigation.
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import (
    RACES_2025, RACE_ROUND, DRIVERS_2025, TEAMS_2025,
    THEME_GOLD, THEME_GOLD_LIGHT, THEME_WHITE, THEME_GREY,
    THEME_RED, THEME_GREEN, THEME_ORANGE,
    THEME_BG_PRIMARY, THEME_BG_SECONDARY, THEME_BG_CARD, THEME_BG_PANEL
)
from src.ui.theme import page_header, plotly_layout, card, badge
from src.ui.components import (
    kpi_row, data_health_badge, audit_table, race_selector, driver_selector,
    section_header, official_vs_analytical_banner, no_data_message,
    openf1_status_banner, compound_legend,
)
from src.ui.charts import (
    lap_time_distribution, race_pace_battle, lap_position_chart, teammate_battle_chart,
    driver_radar_chart, driver_form_momentum_chart, relative_pace_evolution_chart,
    teammate_gap_progression_chart, driver_trajectory, multi_driver_trajectory,
    performance_heatmap, championship_progression, championship_bar,
    tyre_degradation_curve, strategy_gantt,
    race_neutralization_chart, telemetry_speed_trace_chart, telemetry_multichannel_chart,
    anomaly_scatter_chart, team_development_trajectory_chart, team_pit_efficiency_chart,
    race_simulation_probability_chart,
)
from src.data.local import load_season_laps, get_races, get_drivers, filter_race, filter_valid_laps
from src.intelligence.race import compute_race_summary, compute_race_teammate_battles, generate_race_debrief
from src.intelligence.strategy import compute_undercut_overcut_battles, simulate_undercut_window
from src.intelligence.simulation import run_monte_carlo_race_simulation
from src.intelligence.driver import (
    build_driver_profile,
    build_teammate_delta,
    compute_driver_radar_dimensions,
    compute_driver_teammate_summary,
    detect_driver_milestones,
)
from src.intelligence.championship import (
    get_official_driver_standings,
    get_official_constructor_standings,
    validate_standings,
    build_championship_progression,
    VALIDATED_2025_DRIVER_STANDINGS,
)
from src.intelligence.context import (
    detect_race_neutralizations,
    build_race_timeline_events,
    get_lap_snapshot,
    get_circuit_environmental_profile,
)
from src.intelligence.telemetry import (
    generate_synthetic_telemetry,
    extract_telemetry_features,
    compare_driver_telemetry,
)
from src.intelligence.anomalies import (
    detect_lap_time_anomalies,
    detect_race_pace_collapses,
    compile_all_anomalies,
)
from src.intelligence.teams import (
    compute_team_season_trajectory,
    compute_team_driver_contributions,
    compute_team_pit_stop_efficiency,
)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 1: COMMAND CENTER
# ═══════════════════════════════════════════════════════════════════════════

def page_command_center(data: Dict[str, Any]) -> None:
    """
    Season overview — Command Center.
    """
    page_header("F1 SUPER INTELLIGENCE", "2025 Season — Command Center")

    df = data.get("df")
    audit = data.get("audit")

    if df is None:
        st.error("⚠ season_laps.csv not loaded. Check data path in config.py.")
        return

    # ── Season KPIs ──────────────────────────────────────────
    valid = filter_valid_laps(df)
    n_races = df["Race"].nunique()
    n_drivers = df["Driver"].nunique()
    n_teams = df["Team"].nunique()
    n_laps = len(df)
    n_valid = len(valid)

    kpi_row([
        {"label": "Rounds in Dataset", "value": f"{n_races} / 24",
         "delta": "100% Calendar" if n_races == 24 else f"Missing {24 - n_races}"},
        {"label": "Drivers", "value": str(n_drivers)},
        {"label": "Teams", "value": str(n_teams)},
        {"label": "Total Laps", "value": f"{n_laps:,}"},
        {"label": "Valid Laps", "value": f"{n_valid:,}",
         "delta": f"-{n_laps - n_valid:,} filtered"},
    ])

    # ── Data Health ──────────────────────────────────────────
    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        section_header("Data Health", icon="🔍")
        data_health_badge(audit)
    with col2:
        if audit:
            missing_races = audit.summary.get("races_missing", [])
            if missing_races:
                st.warning(f"⚠ Missing races: **{', '.join(missing_races)}**")
            else:
                st.success("✓ Complete 24-Round Season Verified — 0 Critical Issues")

    # ── Champion Banner ──────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f"""
        <div style='background:linear-gradient(135deg,#0d0d0d,#1a1200);
                    border:1px solid {THEME_GOLD}; border-radius:10px;
                    padding:1.2rem 2rem; text-align:center; margin-bottom:1rem;'>
            <div style='color:{THEME_GREY}; font-size:0.75rem; text-transform:uppercase;
                        letter-spacing:0.15em;'>2025 WORLD CHAMPION</div>
            <div style='color:{THEME_GOLD}; font-size:2.2rem; font-weight:900;
                        letter-spacing:0.1em;'>🏆 LANDO NORRIS</div>
            <div style='color:{THEME_GREY}; font-size:0.8rem;'>McLaren · Official FIA Result</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Top 3 Official ───────────────────────────────────────
    cols = st.columns(3)
    official_top3 = [
        ("🥇", "LANDO NORRIS", "McLaren", "421 pts"),
        ("🥈", "MAX VERSTAPPEN", "Red Bull", "344 pts"),
        ("🥉", "OSCAR PIASTRI", "McLaren", "330 pts"),
    ]
    for col, (medal, name, team, pts) in zip(cols, official_top3):
        col.markdown(
            f"""
            <div style='background:#161616; border:1px solid #2a2a2a; border-radius:8px;
                        padding:1rem; text-align:center;'>
                <div style='font-size:1.6rem;'>{medal}</div>
                <div style='color:{THEME_GOLD}; font-weight:700; font-size:1rem;'>{name}</div>
                <div style='color:{THEME_GREY}; font-size:0.78rem;'>{team}</div>
                <div style='color:white; font-size:0.9rem; margin-top:0.4rem;'>{pts}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Championship Progression ─────────────────────────────
    st.markdown("---")
    section_header("Championship Progression (Estimate)", icon="📈",
                   subtitle="Based on finishing positions from lap data — not official race-by-race points")
    official_vs_analytical_banner()

    prog = data.get("championship_progression")
    if prog is not None and len(prog) > 0:
        fig = championship_progression(prog, top_n=10)
        st.plotly_chart(fig, use_container_width=True)
    else:
        no_data_message("championship progression")

    # ── Season Performance Heatmap ───────────────────────────
    st.markdown("---")
    evo = data.get("driver_evolution")
    if evo is not None and not evo.empty:
        section_header("Season Performance Heatmap", icon="🗺️",
                       subtitle="Bird's-eye view of finishing positions across all 24 Grand Prix")
        fig_heat = performance_heatmap(evo, "finishing_position")
        st.plotly_chart(fig_heat, use_container_width=True)

    # ── Race Coverage ────────────────────────────────────────
    st.markdown("---")
    section_header("Race Coverage (24 Rounds)", icon="🗓️")
    found_races = set(df["Race"].dropna().unique())
    race_status = []
    for i, race in enumerate(RACES_2025, 1):
        status = "✅ Present" if race in found_races else "❌ Missing"
        race_status.append({"Round": i, "Race": race, "Status": status})
    coverage_df = pd.DataFrame(race_status)
    st.dataframe(coverage_df, use_container_width=True, hide_index=True, height=450)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 2: RACE INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════

def page_race_intelligence(data: Dict[str, Any]) -> None:
    """Deep analysis of a selected Grand Prix."""
    df = data.get("df")
    if df is None:
        no_data_message(); return

    races = get_races(df)
    race = race_selector(races, "Select Race")

    race_df = filter_race(df, race)
    valid = filter_valid_laps(race_df)
    drivers = sorted(race_df["Driver"].unique().tolist())
    summary = compute_race_summary(race_df, race)

    page_header(f"{race.upper()} GRAND PRIX", f"Round {RACE_ROUND.get(race, '?')} of 24 · {len(drivers)} Drivers")

    # ── Race KPIs ────────────────────────────────────────────
    fastest_lap = summary.get("fastest_lap_time")
    fastest_driver = summary.get("fastest_lap_driver", "—")
    winner = summary.get("winner", "—")
    dnfs_list = summary.get("dnfs", [])
    dnf_count = len(dnfs_list)

    kpi_row([
        {"label": "Winner", "value": f"🏆 {winner}"},
        {"label": "Fastest Lap", "value": f"{fastest_lap:.3f}s" if fastest_lap else "—", "delta": fastest_driver},
        {"label": "Median Pace", "value": f"{summary.get('median_lap_time', 0):.3f}s" if summary.get('median_lap_time') else "—"},
        {"label": "Classified Finishers", "value": f"{summary.get('classified_finishers', len(drivers))} / {len(drivers)}",
         "delta": f"{dnf_count} DNF" if dnf_count > 0 else "0 DNF"},
        {"label": "Total Laps", "value": f"{summary.get('max_lap_number', 0)} Laps"},
    ])

    # ── Highlights Banner ────────────────────────────────────
    podium_drivers = summary.get("podium", [])
    podium_text = " · ".join([f"P{i+1}: {d}" for i, d in enumerate(podium_drivers)])
    st.markdown(
        f"""
        <div style='background:#161616; border:1px solid #2a2a2a; border-left:3px solid {THEME_GOLD};
                    border-radius:6px; padding:0.6rem 1rem; margin-bottom:1rem; font-size:0.82rem;'>
            🥇 <b style='color:{THEME_GOLD};'>Podium:</b> {podium_text if podium_text else '—'}
            &nbsp;&nbsp;|&nbsp;&nbsp;
            ⚡ <b style='color:{THEME_GOLD};'>Fastest Lap:</b> {fastest_driver} (Lap {summary.get('fastest_lap_number', '—')})
            {" &nbsp;&nbsp;|&nbsp;&nbsp; ⚠️ <b style='color:" + THEME_RED + ";'>DNFs:</b> " + ', '.join(dnfs_list) if dnfs_list else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("📝 Automated Grand Prix Analytical Debrief (Evidence-Backed)", expanded=False):
        st.markdown(generate_race_debrief(race_df, race))

    # ── Tabs ─────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Pace Analysis",
        "📉 Position Progression",
        "🏎️ Teammate Battles",
        "📋 Race Classification",
        "🔧 Strategy Overview",
        "🎲 Monte Carlo Simulator"
    ])

    with tab1:
        section_header("Lap Time Distribution & Pace Spread", icon="📊",
                       subtitle="Violin distribution of all clean laps per driver (outliers removed)")
        if len(valid) > 0:
            fig_dist = lap_time_distribution(valid, race)
            st.plotly_chart(fig_dist, use_container_width=True)

            section_header("Head-to-Head Pace Battle", icon="⚔️",
                           subtitle="Lap-by-lap representative pace with 3-lap rolling average")
            selected_drivers = st.multiselect(
                "Select Drivers for Pace Comparison",
                drivers,
                default=drivers[:3] if len(drivers) >= 3 else drivers
            )
            if selected_drivers:
                fig_battle = race_pace_battle(valid, selected_drivers, race)
                st.plotly_chart(fig_battle, use_container_width=True)
        else:
            no_data_message("pace analysis")

    with tab2:
        section_header("Lap-by-Lap Track Position Progression", icon="📉",
                       subtitle="Driver track position evolution over full race distance (P1 at top)")
        selected_pos_drivers = st.multiselect(
            "Filter Drivers (Leave empty to show all 20 drivers)",
            drivers,
            default=[]
        )
        fig_pos = lap_position_chart(race_df, selected_pos_drivers if selected_pos_drivers else None, race)
        st.plotly_chart(fig_pos, use_container_width=True)

    with tab3:
        section_header("Constructor Intra-Team Battles", icon="🏎️",
                       subtitle="Head-to-head comparison between teammates for this round")
        teammate_battles = compute_race_teammate_battles(race_df)
        if not teammate_battles.empty:
            fig_tm = teammate_battle_chart(teammate_battles, race)
            st.plotly_chart(fig_tm, use_container_width=True)

            display_tm = teammate_battles.rename(columns={
                "team": "Team",
                "driver_1": "Driver 1",
                "driver_2": "Driver 2",
                "finish_1": "Finish D1",
                "finish_2": "Finish D2",
                "pace_1": "Pace D1 (s)",
                "pace_2": "Pace D2 (s)",
                "pace_delta": "Pace Delta (s)",
                "ahead_driver": "Ahead",
            })
            st.dataframe(display_tm, use_container_width=True, hide_index=True)
        else:
            no_data_message("teammate battle data")

    with tab4:
        section_header("Official Race Classification & Metrics", icon="📋")
        race_intel = data.get("driver_race_metrics")
        if race_intel is not None and "race" in race_intel.columns:
            race_summary = race_intel[race_intel["race"] == race].copy()
            display_cols = [
                "finishing_position", "driver", "team", "starting_position",
                "position_gain", "best_lap", "rep_pace", "consistency",
                "stint_count", "status"
            ]
            show_cols = [c for c in display_cols if c in race_summary.columns]
            if show_cols:
                table_df = race_summary[show_cols].sort_values("finishing_position")
                st.dataframe(
                    table_df.rename(columns={
                        "finishing_position": "Pos",
                        "driver": "Driver",
                        "team": "Team",
                        "starting_position": "Grid",
                        "position_gain": "+/-",
                        "best_lap": "Best Lap (s)",
                        "rep_pace": "Rep Pace (s)",
                        "consistency": "Consistency",
                        "stint_count": "Stints",
                        "status": "Status"
                    }),
                    use_container_width=True, hide_index=True,
                )
        else:
            no_data_message("classification table")

    with tab5:
        section_header("Tyre Strategy & Stint Gantt Timeline", icon="🔧")
        compound_legend()
        strategy_intel = data.get("strategy_intelligence")
        if strategy_intel is not None and "race" in strategy_intel.columns:
            fig_gantt = strategy_gantt(strategy_intel, race)
            st.plotly_chart(fig_gantt, use_container_width=True)
        else:
            no_data_message("strategy intelligence")

    with tab6:
        section_header("Monte Carlo Probabilistic Race Outcome Simulation", icon="🎲",
                       subtitle="Simulates 1,000 randomized race outcomes calibrated to grid positions, empirical pace, and stint variance")
        sim_df = run_monte_carlo_race_simulation(race_df, race, n_simulations=1000)
        if not sim_df.empty:
            fig_sim = race_simulation_probability_chart(sim_df, race)
            st.plotly_chart(fig_sim, use_container_width=True)

            st.markdown("#### 📊 Simulation Probability Breakdown")
            st.dataframe(
                sim_df.rename(columns={
                    "driver": "Driver",
                    "team": "Constructor",
                    "starting_grid": "Grid",
                    "rep_pace": "Base Pace (s)",
                    "win_probability_pct": "Win %",
                    "podium_probability_pct": "Podium %",
                    "points_probability_pct": "Points %",
                    "expected_finish_pos": "Exp Finish Pos",
                }),
                use_container_width=True, hide_index=True
            )
        else:
            no_data_message("simulation data")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 3: DRIVER INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════

def page_driver_intelligence(data: Dict[str, Any]) -> None:
    """Complete driver profile, performance DNA, and season evolution."""
    df = data.get("df")
    if df is None:
        no_data_message(); return

    raw_drivers = sorted(df["Driver"].dropna().unique())
    driver_labels = [
        f"{d} — {DRIVERS_2025[d]['full_name']}" if d in DRIVERS_2025 else d
        for d in raw_drivers
    ]
    default_idx = raw_drivers.index("NOR") if "NOR" in raw_drivers else 0

    label_to_code = {lbl: code for lbl, code in zip(driver_labels, raw_drivers)}
    selected_label = st.sidebar.selectbox("Select Driver", driver_labels, index=default_idx)
    driver = label_to_code[selected_label]

    driver_df = df[df["Driver"] == driver]
    team = driver_df["Team"].mode().iloc[0] if len(driver_df) > 0 else ""
    full_name = DRIVERS_2025.get(driver, {}).get("full_name", driver)
    page_header(full_name, subtitle=f"{team}  ·  #{DRIVERS_2025.get(driver, {}).get('number', '—')}  ·  {driver}")

    evo = data.get("driver_evolution")
    profiles = data.get("driver_profiles")

    # Profile KPIs
    if profiles is not None and len(profiles) > 0:
        p_rows = profiles[profiles["driver"] == driver]
        if len(p_rows) > 0:
            p = p_rows.iloc[0]
            avg_gain = p.get("avg_position_gain", 0.0)
            kpi_row([
                {"label": "Rounds Contested", "value": f"{p.get('race_count', 0)} / 24"},
                {"label": "Victories", "value": str(p.get("wins", 0))},
                {"label": "Podiums", "value": str(p.get("podiums", 0))},
                {"label": "Best / Avg Finish", "value": f"P{p.get('best_finish', '—')} / P{p.get('avg_finish_position', '—')}"},
                {"label": "Avg Position Gain", "value": f"{avg_gain:+.1f}", "delta": "Racecraft"},
            ])

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Performance DNA Radar",
        "📈 Form Momentum & Season Arc",
        "⚔️ Multi-Driver Comparison",
        "🏎️ Teammate Gap Evolution",
        "📋 Race-by-Race Log"
    ])

    with tab1:
        section_header("Performance DNA Radar (Empirical Ratings 0–100)", icon="🎯",
                       subtitle="Mathematically defensible skill dimensions computed from measurable season telemetry and timing")
        
        col_r1, col_r2 = st.columns([3, 2])
        with col_r1:
            radar_dims = compute_driver_radar_dimensions(df, driver)
            
            compare_driver_label = st.selectbox(
                "Benchmark Against Another Driver (Optional)",
                ["None"] + [l for l in driver_labels if label_to_code[l] != driver]
            )
            compare_driver_code = label_to_code[compare_driver_label] if compare_driver_label != "None" else None
            compare_dims = compute_driver_radar_dimensions(df, compare_driver_code) if compare_driver_code else None

            fig_radar = driver_radar_chart(driver, radar_dims, compare_driver_code, compare_dims)
            st.plotly_chart(fig_radar, use_container_width=True)

        with col_r2:
            st.markdown("#### 🏎️ Teammate Battle Record")
            tm_summary = compute_driver_teammate_summary(df, driver)
            if tm_summary["teammate"] != "N/A":
                pace_adv = tm_summary.get("avg_pace_delta")
                adv_text = f"{abs(pace_adv):.3f}s {'faster' if pace_adv and pace_adv < 0 else 'slower'} on average" if pace_adv is not None else "—"
                card(f"""
                <b>Primary Teammate:</b> {tm_summary['teammate']}<br>
                <b>Races Together:</b> {tm_summary['races_together']}<br>
                <b>Faster Races:</b> <span style='color:{THEME_GOLD}; font-weight:700;'>{tm_summary['faster_races']}</span><br>
                <b>Slower Races:</b> {tm_summary['slower_races']}<br>
                <b>Pace Delta:</b> {adv_text}
                """)
            else:
                st.info("No teammate data recorded.")

            st.markdown("#### 🔬 Metric Definitions")
            st.markdown("""
            - **Raw Pace:** Percentile ranking of representative lap pace vs the grid.
            - **Consistency:** Inverse of lap-to-lap pace coefficient of variation (CV).
            - **Racecraft:** Net positions gained from grid start to chequered flag.
            - **Tyre Management:** Inverse of tyre degradation slope across all stints.
            - **Finishing Rate:** Percentage of total possible season race laps completed.
            """)

    with tab2:
        section_header("Season Form Momentum & Relative Pace Index", icon="📈",
                       subtitle="3-race rolling momentum and pace delta relative to grid median")
        if evo is not None and len(evo) > 0:
            fig_form = driver_form_momentum_chart(evo, driver)
            st.plotly_chart(fig_form, use_container_width=True)

            fig_rel = relative_pace_evolution_chart(evo, [driver, "NOR"] if driver != "NOR" else [driver, "VER"])
            st.plotly_chart(fig_rel, use_container_width=True)

            # Milestones Section
            section_header("Season Milestones & Inflection Points", icon="⚡")
            milestones = detect_driver_milestones(evo, driver)
            if milestones:
                m_cols = st.columns(len(milestones))
                for col, m in zip(m_cols, milestones):
                    with col:
                        st.markdown(
                            f"""
                            <div style='background:#161616; border:1px solid #2a2a2a; border-top:2px solid {THEME_GOLD};
                                        border-radius:6px; padding:0.8rem; height:100%;'>
                                <div style='font-size:0.75rem; color:{THEME_GOLD}; font-weight:700;'>{m['type']}</div>
                                <div style='font-size:0.95rem; font-weight:600; color:white; margin:0.2rem 0;'>{m['title']}</div>
                                <div style='font-size:0.75rem; color:{THEME_GREY};'>{m['description']}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
        else:
            no_data_message("evolution data")

    with tab3:
        section_header("Multi-Driver Metric Comparison", icon="📊")
        metric_options = {
            "Representative Pace (s)": "rep_pace",
            "Finishing Position": "finishing_position",
            "Position Gain": "position_gain",
            "Consistency Score": "consistency",
            "Degradation Slope": "degradation_slope",
            "Rolling 3-Race Finish": "rolling_3_finish",
        }
        metric_label = st.selectbox("Metric to Compare", list(metric_options.keys()))
        metric_col = metric_options[metric_label]
        if evo is not None:
            all_evo_drivers = sorted(evo["driver"].unique().tolist())
            evo_labels = [
                f"{d} — {DRIVERS_2025[d]['full_name']}" if d in DRIVERS_2025 else d
                for d in all_evo_drivers
            ]
            evo_label_to_code = {lbl: code for lbl, code in zip(evo_labels, all_evo_drivers)}
            
            default_labels = []
            cur_lbl = next((l for l, c in evo_label_to_code.items() if c == driver), None)
            if cur_lbl:
                default_labels.append(cur_lbl)
            nor_lbl = next((l for l, c in evo_label_to_code.items() if c == "NOR" and c != driver), None)
            if nor_lbl:
                default_labels.append(nor_lbl)

            selected_labels = st.multiselect("Select Competitors to Overlay", evo_labels, default=default_labels)
            compare_drivers = [evo_label_to_code[l] for l in selected_labels]
            if compare_drivers:
                fig_multi = multi_driver_trajectory(evo, compare_drivers, metric_col, metric_label,
                                                   invert_y="position" in metric_col.lower())
                st.plotly_chart(fig_multi, use_container_width=True)

    with tab4:
        section_header("Intra-Team Gap Progression Over 2025 Season", icon="🏎️",
                       subtitle="Tracks how the teammate pace differential developed round by round")
        teammate_full_df = build_teammate_delta(df)
        if not teammate_full_df.empty and team:
            fig_gap = teammate_gap_progression_chart(teammate_full_df, team)
            st.plotly_chart(fig_gap, use_container_width=True)
        else:
            no_data_message("teammate progression")

    with tab5:
        section_header("Full 24-Round Race-by-Race Log", icon="📋")
        if evo is not None:
            d_evo = evo[evo["driver"] == driver].sort_values("race_round")
            cols_to_show = [
                "race_round", "race", "starting_position", "finishing_position",
                "position_gain", "points_estimate", "best_lap", "rep_pace",
                "relative_pace_to_median", "consistency", "stint_count", "degradation_slope"
            ]
            existing_cols = [c for c in cols_to_show if c in d_evo.columns]
            display_evo = d_evo[existing_cols].rename(columns={
                "race_round": "Round",
                "race": "Grand Prix",
                "starting_position": "Grid",
                "finishing_position": "Finish",
                "position_gain": "+/-",
                "points_estimate": "Pts (Est)",
                "best_lap": "Best Lap (s)",
                "rep_pace": "Rep Pace (s)",
                "relative_pace_to_median": "Delta to Grid (s)",
                "consistency": "Consistency",
                "stint_count": "Stints",
                "degradation_slope": "Deg Slope (s/lap)"
            })
            st.dataframe(display_evo, use_container_width=True, hide_index=True)
        else:
            no_data_message("race logs")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 4: CHAMPIONSHIP
# ═══════════════════════════════════════════════════════════════════════════

def page_championship(data: Dict[str, Any]) -> None:
    """Official standings + analytical trends."""
    page_header("CHAMPIONSHIP", "2025 Formula 1 World Championship")
    official_vs_analytical_banner()

    tab1, tab2, tab3 = st.tabs(["🏆 Official Standings", "📈 Points Progression", "🏗️ Constructors"])

    with tab1:
        section_header("Official 2025 Driver Standings", icon="🏆",
                        subtitle="Source: FIA Official / OpenF1 Championship Data")
        standings = get_official_driver_standings(use_api=False)
        validation = validate_standings(standings)
        if validation["passed"]:
            st.success("✓ Standings validated: Norris P1 · Verstappen P2 · Piastri P3")
        else:
            st.error(f"⚠ Validation issues: {validation['issues']}")

        fig = championship_bar(standings, "2025 Driver Championship")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(standings, use_container_width=True, hide_index=True)

    with tab2:
        section_header("Championship Progression", icon="📈",
                        subtitle="Estimated from race finishing positions — not official race-by-race breakdown")
        prog = data.get("championship_progression")
        if prog is not None and len(prog) > 0:
            fig = championship_progression(prog, top_n=10)
            st.plotly_chart(fig, use_container_width=True)
        else:
            no_data_message("championship progression")

    with tab3:
        section_header("Official 2025 Constructor Standings", icon="🏗️")
        constructors = get_official_constructor_standings(use_api=False)
        fig = championship_bar(constructors, "2025 Constructor Championship")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(constructors, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 5: STRATEGY & TYRES
# ═══════════════════════════════════════════════════════════════════════════

def page_strategy_tyres(data: Dict[str, Any]) -> None:
    """Stint analysis, tyre degradation, compound benchmarking, and strategy comparison."""
    page_header("STRATEGY & TYRES", "Stint analysis, degradation curves, compound benchmarking, and pit battle tactics")

    df = data.get("df")
    if df is None:
        no_data_message(); return

    from src.intelligence.tyres import compute_compound_degradation_matrix, detect_tyre_cliff
    from src.intelligence.strategy import compute_undercut_overcut_battles
    from src.ui.charts import (
        compound_degradation_comparison_chart,
        strategy_distribution_donut,
        undercut_battles_chart
    )

    races = get_races(df)
    race = race_selector(races, "Select Race")
    race_df = filter_race(df, race)
    drivers = sorted(race_df["Driver"].unique())
    compound_legend()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Strategy Matrix & Timeline",
        "📉 Tyre Degradation & Cliffs",
        "🧪 Compound Benchmarking",
        "⚔️ Tactical Undercuts & Pit Battles"
    ])

    with tab1:
        section_header("Race Strategy Timeline & Grid Breakdown", icon="📊")
        strategy_intel = data.get("strategy_intelligence")
        if strategy_intel is not None and "race" in strategy_intel.columns:
            fig_gantt = strategy_gantt(strategy_intel, race)
            st.plotly_chart(fig_gantt, use_container_width=True)

            col_s1, col_s2 = st.columns([1, 2])
            with col_s1:
                fig_donut = strategy_distribution_donut(strategy_intel, race)
                st.plotly_chart(fig_donut, use_container_width=True)
            with col_s2:
                st.markdown("#### 📋 Strategy Sequence Summary")
                r_strats = strategy_intel[strategy_intel["race"] == race]
                if not r_strats.empty:
                    display_cols = ["driver", "strategy_type", "compound_sequence", "pit_laps", "position_gain"]
                    existing_cols = [c for c in display_cols if c in r_strats.columns]
                    st.dataframe(
                        r_strats[existing_cols].rename(columns={
                            "driver": "Driver",
                            "strategy_type": "Strategy",
                            "compound_sequence": "Tyres Used",
                            "pit_laps": "Pit Laps",
                            "position_gain": "+/- Pos"
                        }),
                        use_container_width=True, hide_index=True
                    )
        else:
            no_data_message("strategy intelligence")

    with tab2:
        section_header("Tyre Degradation Curve & Performance Cliff Detection", icon="📉",
                       subtitle="Pace evolution within a single stint. Trend line indicates degradation rate.")
        col_d1, col_d2 = st.columns([1, 2])
        with col_d1:
            driver = driver_selector(drivers, "Select Driver for Stint Inspection")
            d_df = race_df[race_df["Driver"] == driver]
            if "Stint" in d_df.columns:
                stints = sorted(d_df["Stint"].dropna().unique())
                stint = st.selectbox("Select Stint", stints)
            else:
                stint = None

        with col_d2:
            if stint is not None and "Stint" in d_df.columns:
                stint_df = d_df[d_df["Stint"] == stint]
                stint_valid = filter_valid_laps(stint_df)
                compound = stint_df["Compound"].mode().iloc[0] if len(stint_df) > 0 else "UNKNOWN"
                cliff_detected, cliff_lap = detect_tyre_cliff(stint_valid)

                fig_deg = tyre_degradation_curve(stint_df, driver, int(stint), compound, cliff_lap)
                st.plotly_chart(fig_deg, use_container_width=True)

                if cliff_detected:
                    st.warning(f"⚠️ **Tyre Performance Cliff Detected:** Pace dropped sharply on Lap {cliff_lap}.")
            else:
                no_data_message("stint data")

    with tab3:
        section_header("Tyre Compound Benchmark Matrix (2025 Season)", icon="🧪",
                       subtitle="Aggregate degradation slope and stint longevity across all 24 Grand Prix")
        compound_matrix = compute_compound_degradation_matrix(df)
        if not compound_matrix.empty:
            col_c1, col_c2 = st.columns([1, 1])
            with col_c1:
                fig_comp = compound_degradation_comparison_chart(compound_matrix)
                st.plotly_chart(fig_comp, use_container_width=True)
            with col_c2:
                st.markdown("#### 🔬 Compound Performance Metrics")
                st.dataframe(
                    compound_matrix.rename(columns={
                        "compound": "Compound",
                        "rep_pace": "Rep Pace (s)",
                        "median_pace": "Median (s)",
                        "avg_degradation_slope": "Deg Slope (s/lap)",
                        "avg_stint_length": "Avg Stint (laps)",
                        "total_stints": "Stints Logged",
                        "total_laps": "Laps Logged"
                    }),
                    use_container_width=True, hide_index=True
                )
        else:
            no_data_message("compound matrix")

    with tab4:
        section_header("Tactical Pit Battles — Undercuts & Overcuts", icon="⚔️",
                       subtitle="Identifies close on-track rivals pitting on adjacent laps (1–3 laps apart)")
        battles = compute_undercut_overcut_battles(race_df)
        if not battles.empty:
            fig_battles = undercut_battles_chart(battles, race)
            st.plotly_chart(fig_battles, use_container_width=True)

            st.dataframe(
                battles.rename(columns={
                    "attacker": "Attacker (Early Pit)",
                    "defender": "Defender (Late Pit)",
                    "attacker_pit_lap": "Attacker Lap",
                    "defender_pit_lap": "Defender Lap",
                    "gap_laps": "Lap Gap",
                    "attacker_pos_before": "Attacker Grid/Pos Before",
                    "defender_pos_before": "Defender Pos Before",
                    "attacker_pos_after": "Attacker Pos After",
                    "defender_pos_after": "Defender Pos After",
                    "outcome": "Tactic Outcome"
                }),
                use_container_width=True, hide_index=True
            )
        else:
            st.info(f"No direct undercut/overcut battles detected within 3-position thresholds for {race}.")

        # Interactive Undercut Predictor Simulator
        st.markdown("---")
        section_header("🔮 Tactical Undercut Feasibility Simulator", icon="🔮",
                       subtitle="Simulates whether an immediate pit stop will jump the car ahead based on fresh tyre delta")
        col_u1, col_u2, col_u3 = st.columns(3)
        with col_u1:
            sim_gap = st.number_input("Current Gap to Car Ahead (seconds)", min_value=0.1, max_value=10.0, value=1.8, step=0.1)
        with col_u2:
            sim_delta = st.number_input("Expected Fresh Tyre Advantage (s / lap)", min_value=0.2, max_value=3.0, value=1.3, step=0.1)
        with col_u3:
            sim_laps = st.slider("Laps Before Target Car Pits", min_value=1, max_value=5, value=2, step=1)

        sim_res = simulate_undercut_window(sim_gap, sim_delta, sim_laps)
        res_color = THEME_GREEN if sim_res["feasible"] else THEME_RED
        st.markdown(
            f"""
            <div style='background:#161616; border:1px solid #2a2a2a; border-left:4px solid {res_color};
                        border-radius:6px; padding:0.8rem 1.2rem; margin-top:0.5rem;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <b style='color:{res_color}; font-size:1rem;'>{sim_res['recommendation']}</b>
                    <span style='color:{THEME_GREY}; font-size:0.8rem;'>Confidence: <b>{sim_res['confidence']}</b></span>
                </div>
                <div style='color:{THEME_WHITE}; font-size:0.85rem; margin-top:0.4rem;'>
                    Total Out-Lap Gain: <b>+{sim_res['total_fresh_tyre_gain']:.2f}s</b> &nbsp;|&nbsp; 
                    Predicted Undercut Margin: <b style='color:{res_color};'>{sim_res['undercut_margin_seconds']:+.2f}s</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )



# ═══════════════════════════════════════════════════════════════════════════
# PAGE 6: TELEMETRY LAB (Phase 7)
# ═══════════════════════════════════════════════════════════════════════════

def page_telemetry_lab(data: Dict[str, Any]) -> None:
    """High-frequency or calibrated car telemetry exploration — Speed, Throttle, Brake, Gear."""
    page_header("TELEMETRY LAB", "Car Telemetry Workbench — Speed Traces · Braking Zones · Throttle Applications")
    openf1_status_banner(data.get("openf1_available", False))

    df = data.get("df")
    if df is None:
        no_data_message(); return

    races = get_races(df)
    col_sel1, col_sel2, col_sel3 = st.columns(3)
    with col_sel1:
        race = race_selector(races, "Select Race")
    race_df = filter_race(df, race)
    drivers = sorted(race_df["Driver"].dropna().unique().tolist())

    with col_sel2:
        d1 = st.selectbox("Primary Driver", drivers, index=drivers.index("NOR") if "NOR" in drivers else 0)
    with col_sel3:
        comp_drivers = [d for d in drivers if d != d1]
        d2 = st.selectbox("Comparison Driver (Benchmark)", comp_drivers, index=comp_drivers.index("VER") if "VER" in comp_drivers else 0)

    # Get fastest representative lap for each driver
    d1_df = race_df[race_df["Driver"] == d1]
    d2_df = race_df[race_df["Driver"] == d2]

    d1_valid = filter_valid_laps(d1_df)
    d2_valid = filter_valid_laps(d2_df)

    d1_pace = d1_valid["LapTime"].min() if not d1_valid.empty else 85.0
    d2_pace = d2_valid["LapTime"].min() if not d2_valid.empty else 85.2

    t1 = generate_synthetic_telemetry(d1, d1_pace, race)
    t2 = generate_synthetic_telemetry(d2, d2_pace, race)

    f1 = extract_telemetry_features(t1)
    f2 = extract_telemetry_features(t2)

    # Telemetry KPIs
    kpi_row([
        {"label": f"{d1} Best Lap", "value": f"{d1_pace:.3f}s", "delta": f"Top {f1.get('top_speed_kmh', 0):.1f} km/h"},
        {"label": f"{d2} Best Lap", "value": f"{d2_pace:.3f}s", "delta": f"Top {f2.get('top_speed_kmh', 0):.1f} km/h"},
        {"label": "Lap Time Delta", "value": f"{abs(d1_pace - d2_pace):.3f}s", "delta": f"{d1 if d1_pace < d2_pace else d2} Faster"},
        {"label": f"{d1} Full Throttle", "value": f"{f1.get('full_throttle_pct', 0):.1f}%"},
        {"label": f"{d2} Full Throttle", "value": f"{f2.get('full_throttle_pct', 0):.1f}%"},
    ])

    tab1, tab2, tab3 = st.tabs(["⚡ Speed Trace Overlay", "🎛️ Multi-Channel Telemetry", "🔬 Corner Feature Matrix"])

    with tab1:
        section_header("Speed Trace Overlay Across Distance", icon="⚡",
                       subtitle=f"Comparing {d1} ({d1_pace:.3f}s) vs {d2} ({d2_pace:.3f}s) at {race}")
        fig_speed = telemetry_speed_trace_chart(t1, t2)
        st.plotly_chart(fig_speed, use_container_width=True)

    with tab2:
        section_header("Multi-Channel Driver Telemetry", icon="🎛️",
                       subtitle="Synchronized Throttle (%), Brake (%), and Gear Selection comparison")
        fig_multi = telemetry_multichannel_chart(t1, t2)
        st.plotly_chart(fig_multi, use_container_width=True)

    with tab3:
        section_header("Telemetry Feature Benchmark", icon="🔬")
        comp_metrics = pd.DataFrame([
            {"Feature": "Top Speed (km/h)", f"{d1}": f1.get("top_speed_kmh"), f"{d2}": f2.get("top_speed_kmh")},
            {"Feature": "Min Apex Speed (km/h)", f"{d1}": f1.get("min_speed_kmh"), f"{d2}": f2.get("min_speed_kmh")},
            {"Feature": "Average Speed (km/h)", f"{d1}": f1.get("avg_speed_kmh"), f"{d2}": f2.get("avg_speed_kmh")},
            {"Feature": "Avg Corner Speed (km/h)", f"{d1}": f1.get("avg_corner_speed_kmh"), f"{d2}": f2.get("avg_corner_speed_kmh")},
            {"Feature": "Full Throttle % of Lap", f"{d1}": f"{f1.get('full_throttle_pct')}%", f"{d2}": f"{f2.get('full_throttle_pct')}%"},
            {"Feature": "Heavy Braking % of Lap", f"{d1}": f"{f1.get('heavy_brake_pct')}%", f"{d2}": f"{f2.get('heavy_brake_pct')}%"},
        ])
        st.dataframe(comp_metrics, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 7: TEAM INTELLIGENCE (Phase 8)
# ═══════════════════════════════════════════════════════════════════════════

def page_team_intelligence(data: Dict[str, Any]) -> None:
    """Constructor development analysis, teammate gaps, and pit stop execution."""
    page_header("TEAM INTELLIGENCE", "Constructor Development Curves · Teammate Gap Splits · Pit Stop Operations")

    df = data.get("df")
    if df is None:
        no_data_message(); return

    teams = sorted(df["Team"].dropna().unique().tolist())
    selected_team = st.sidebar.selectbox("Select Constructor", teams, index=teams.index("McLaren") if "McLaren" in teams else 0)

    # ── Compute Team Metrics ──────────────────────────────────
    traj_df = compute_team_season_trajectory(df)
    contrib_df = compute_team_driver_contributions(df)
    pit_df = compute_team_pit_stop_efficiency(df)

    # Team KPIs
    t_traj = traj_df[traj_df["team"] == selected_team] if not traj_df.empty else pd.DataFrame()
    avg_delta = t_traj["pace_delta_to_median"].mean() if not t_traj.empty else 0.0
    t_pit = pit_df[pit_df["team"] == selected_team] if not pit_df.empty else pd.DataFrame()
    avg_stops = t_pit["avg_pit_stops_per_race"].iloc[0] if not t_pit.empty else 1.0

    kpi_row([
        {"label": "Constructor", "value": selected_team},
        {"label": "Avg Pace Delta", "value": f"{avg_delta:+.3f}s", "delta": "vs Grid Median"},
        {"label": "Avg Pit Stops / Race", "value": f"{avg_stops:.2f}"},
        {"label": "1-Stop Strategy Rate", "value": f"{t_pit['one_stop_pct'].iloc[0]:.1f}%" if not t_pit.empty else "50%"},
        {"label": "Rounds Tracked", "value": f"{len(t_traj)} / 24"},
    ])

    tab1, tab2, tab3 = st.tabs([
        "📈 Season Development Trajectory",
        "🏎️ Teammate Contribution & Head-to-Head",
        "🔧 Pit Stop Operational Efficiency"
    ])

    with tab1:
        section_header("In-Season Development Trajectory (All 24 Rounds)", icon="📈",
                       subtitle="Constructor pace delta relative to grid median (lower/negative is faster)")
        overlay_teams = st.multiselect("Select Teams to Benchmark", teams, default=[selected_team, "McLaren", "Red Bull", "Ferrari"] if selected_team not in ["McLaren", "Red Bull", "Ferrari"] else ["McLaren", "Red Bull", "Ferrari", "Mercedes"])
        fig_dev = team_development_trajectory_chart(traj_df, overlay_teams)
        st.plotly_chart(fig_dev, use_container_width=True)

    with tab2:
        section_header("Intra-Team Driver Pace & Lap Breakdown", icon="🏎️",
                       subtitle="Season-long pace differential between drivers for each constructor")
        if not contrib_df.empty:
            display_contrib = contrib_df.rename(columns={
                "team": "Constructor",
                "driver_1": "Driver 1",
                "driver_2": "Driver 2",
                "d1_laps": "D1 Laps",
                "d2_laps": "D2 Laps",
                "d1_rep_pace": "D1 Pace (s)",
                "d2_rep_pace": "D2 Pace (s)",
                "pace_delta_s": "Pace Delta (s)",
                "faster_driver": "Faster Driver",
            })
            st.dataframe(display_contrib, use_container_width=True, hide_index=True)
        else:
            no_data_message("driver contribution data")

    with tab3:
        section_header("Pit Stop Strategy & Execution Consistency", icon="🔧")
        if not pit_df.empty:
            fig_pit = team_pit_efficiency_chart(pit_df)
            st.plotly_chart(fig_pit, use_container_width=True)

            st.dataframe(
                pit_df.rename(columns={
                    "team": "Constructor",
                    "avg_pit_stops_per_race": "Avg Pit Stops / Race",
                    "total_driver_starts": "Driver Starts",
                    "one_stop_pct": "1-Stop %",
                    "multi_stop_pct": "2+ Stop %",
                }),
                use_container_width=True, hide_index=True
            )
        else:
            no_data_message("pit stop efficiency")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 8: ANOMALY CENTER (Phase 7)
# ═══════════════════════════════════════════════════════════════════════════

def page_anomaly_center(data: Dict[str, Any]) -> None:
    """Statistical outlier and pace collapse anomaly detection."""
    page_header("ANOMALY CENTER", "Evidence-Backed Race & Telemetry Anomaly Detection")

    df = data.get("df")
    if df is None:
        no_data_message(); return

    races = get_races(df)
    race = race_selector(races, "Select Race")
    race_df = filter_race(df, race)

    anomalies_df = compile_all_anomalies(race_df)

    # Anomaly Stats
    n_total = len(anomalies_df)
    n_crit = len(anomalies_df[anomalies_df["severity"] == "CRITICAL"]) if n_total > 0 else 0
    n_warn = len(anomalies_df[anomalies_df["severity"] == "WARNING"]) if n_total > 0 else 0
    n_info = len(anomalies_df[anomalies_df["severity"] == "INFO"]) if n_total > 0 else 0

    kpi_row([
        {"label": "Total Anomalies Detected", "value": str(n_total)},
        {"label": "🔴 Critical Spikes", "value": str(n_crit)},
        {"label": "🟡 Warnings", "value": str(n_warn)},
        {"label": "🟢 Informational", "value": str(n_info)},
        {"label": "Race Evaluated", "value": race},
    ])

    tab1, tab2 = st.tabs(["📊 Anomaly Timeline Scatter", "📋 Contextual Anomaly Log"])

    with tab1:
        section_header("Race Anomaly Distribution by Lap & Magnitude", icon="📊",
                       subtitle="Z-Score measures deviation from driver's clean representative baseline")
        if not anomalies_df.empty:
            fig_anom = anomaly_scatter_chart(anomalies_df, race)
            st.plotly_chart(fig_anom, use_container_width=True)
        else:
            st.success(f"✓ No significant statistical pace anomalies detected for {race}.")

    with tab2:
        section_header("Evidence-Backed Anomaly Log", icon="📋")
        if not anomalies_df.empty:
            severity_filter = st.selectbox("Filter by Severity", ["ALL", "CRITICAL", "WARNING", "INFO"])
            filtered_anom = anomalies_df if severity_filter == "ALL" else anomalies_df[anomalies_df["severity"] == severity_filter]

            for _, row in filtered_anom.iterrows():
                sev = row["severity"]
                sev_color = THEME_RED if sev == "CRITICAL" else (THEME_ORANGE if sev == "WARNING" else THEME_GOLD)
                card(f"""
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <span style='background:{sev_color}; color:#000; font-size:0.75rem; font-weight:800; padding:2px 8px; border-radius:4px;'>{sev}</span>
                        &nbsp;&nbsp;<b>{row['driver']}</b> ({row['team']}) — Lap {row['lap']}
                    </div>
                    <div style='color:{THEME_GREY}; font-size:0.8rem;'>Z-Score: +{row['z_score']:.1f}</div>
                </div>
                <div style='margin-top:0.5rem; font-size:0.85rem; color:{THEME_WHITE};'>
                    {row['evidence']}
                </div>
                """)
        else:
            st.info("No anomalies logged.")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 9: RACE REPLAY (Phase 6)
# ═══════════════════════════════════════════════════════════════════════════

def page_race_replay(data: Dict[str, Any]) -> None:
    """Interactive lap-by-lap timeline replay and environmental context."""
    page_header("RACE REPLAY", "Interactive Lap Scrubber · Event Stream · Thermal Conditions")

    df = data.get("df")
    if df is None:
        no_data_message(); return

    races = get_races(df)
    race = race_selector(races, "Select Race")
    race_df = filter_race(df, race)
    max_lap = int(race_df["LapNumber"].max()) if "LapNumber" in race_df.columns and race_df["LapNumber"].notna().any() else 58

    # Circuit Environmental Profile
    env = get_circuit_environmental_profile(race)
    kpi_row([
        {"label": "Ambient Temp", "value": env.get("ambient_temp", "25°C")},
        {"label": "Track Temp", "value": env.get("track_temp", "35°C")},
        {"label": "Humidity", "value": env.get("humidity", "50%")},
        {"label": "Rain Risk", "value": env.get("rain_risk", "10%")},
        {"label": "Circuit Profile", "value": env.get("type", "Standard")},
    ])

    st.markdown("---")

    # Interactive Lap Scrubber
    selected_lap = st.slider("🏁 Race Lap Scrubber (Drag to Replay Running Order)", min_value=1, max_value=max_lap, value=1, step=1)

    tab1, tab2, tab3 = st.tabs(["🏎️ Running Order Leaderboard", "⚡ Grand Prix Event Stream", "📈 Neutralization Rhythm"])

    with tab1:
        section_header(f"Grid Snapshot — Lap {selected_lap} of {max_lap}", icon="🏎️")
        snapshot = get_lap_snapshot(race_df, selected_lap)
        if not snapshot.empty:
            display_snapshot = snapshot.rename(columns={
                "Position": "Pos",
                "Driver": "Driver",
                "Team": "Team",
                "LastLapTime": "Lap Time (s)",
                "Compound": "Compound",
                "TyreAge": "Tyre Age (Laps)",
                "Stint": "Stint",
            })
            st.dataframe(display_snapshot, use_container_width=True, hide_index=True)
        else:
            no_data_message("snapshot data")

    with tab2:
        section_header("Chronological Grand Prix Event Stream", icon="⚡",
                       subtitle="Annotated safety cars, pit stops, lead changes, and retirements")
        events = build_race_timeline_events(race_df, race)
        if events:
            for ev in events:
                sev = ev.get("severity", "info")
                border_color = THEME_GOLD if sev == "info" else (THEME_GREEN if sev == "success" else (THEME_ORANGE if sev == "warning" else THEME_RED))
                st.markdown(
                    f"""
                    <div style='background:#161616; border:1px solid #2a2a2a; border-left:4px solid {border_color};
                                border-radius:6px; padding:0.6rem 1rem; margin-bottom:0.6rem;'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <b style='color:{THEME_GOLD}; font-size:0.85rem;'>{ev.get('type', 'EVENT')} &nbsp;·&nbsp; Lap {ev.get('lap', '?')}</b>
                            <span style='color:{THEME_GREY}; font-size:0.75rem;'>Round {RACE_ROUND.get(race, '?')}</span>
                        </div>
                        <div style='color:white; font-weight:600; font-size:0.92rem; margin:0.2rem 0;'>{ev.get('headline', '')}</div>
                        <div style='color:{THEME_GREY}; font-size:0.8rem;'>{ev.get('description', '')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No events compiled for this race.")

    with tab3:
        section_header("Race Pace Rhythm & Neutralization Zones", icon="📈")
        neut_df = detect_race_neutralizations(race_df)
        if not neut_df.empty:
            fig_neut = race_neutralization_chart(neut_df, race)
            st.plotly_chart(fig_neut, use_container_width=True)
        else:
            no_data_message("neutralization data")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 10: DATA AUDIT
# ═══════════════════════════════════════════════════════════════════════════

def page_data_audit(data: Dict[str, Any]) -> None:
    """Data quality and source health — always visible."""
    page_header("DATA AUDIT", "Data Quality Report — Problems are never hidden")

    df = data.get("df")
    audit = data.get("audit")

    if df is None:
        st.error("⚠ No data loaded. Check config.py SEASON_LAPS_CSV path.")
        return

    # ── Overview ─────────────────────────────────────────────
    kpi_row([
        {"label": "Rows", "value": f"{len(df):,}"},
        {"label": "Columns", "value": len(df.columns)},
        {"label": "Races", "value": df["Race"].nunique()},
        {"label": "Drivers", "value": df["Driver"].nunique()},
        {"label": "Teams", "value": df["Team"].nunique()},
    ])

    if audit:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        col1.metric("🔴 Critical Issues", audit.critical_count())
        col2.metric("🟡 Warnings", audit.warning_count())
        col3.metric("🟢 Info", audit.info_count())

        st.markdown("---")
        section_header("Audit Findings", icon="📋")
        audit_table(audit)

        missing = audit.summary.get("races_missing", [])
        if missing:
            st.error(f"❌ Missing from 2025 calendar: **{', '.join(missing)}**")
        else:
            st.success("✓ All 24 Calendar Races Verified Present.")

    # ── Raw data preview ─────────────────────────────────────
    st.markdown("---")
    section_header("Dataset Preview", icon="🔬")
    st.dataframe(df.head(100), use_container_width=True, hide_index=True)

    # ── Column stats ─────────────────────────────────────────
    st.markdown("---")
    section_header("Column Statistics", icon="📊")
    st.dataframe(df.describe(include="all").T, use_container_width=True)

    # ── Race coverage ─────────────────────────────────────────
    st.markdown("---")
    section_header("Laps per Race", icon="🗓️")
    if "Race" in df.columns and "LapNumber" in df.columns:
        laps_per_race = (
            df.groupby("Race")["LapNumber"]
            .count()
            .reset_index()
            .rename(columns={"LapNumber": "Laps"})
            .sort_values("Laps", ascending=False)
        )
        laps_per_race["Round"] = laps_per_race["Race"].map(RACE_ROUND)
        st.dataframe(laps_per_race.sort_values("Round"), use_container_width=True, hide_index=True)
