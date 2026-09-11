"""
src/ui/charts.py — Plotly Chart Builders for F1 Super Intelligence
===================================================================
All chart functions return Plotly Figure objects.
Charts are interactive, tooltipped, consistent, and use the platform theme.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import (
    COMPOUND_COLORS, THEME_GOLD, THEME_GOLD_LIGHT, THEME_WHITE, THEME_GREY,
    THEME_RED, THEME_GREEN, THEME_ORANGE,
    THEME_BG_PRIMARY, THEME_BG_SECONDARY, THEME_BG_CARD, THEME_BG_PANEL
)
from src.ui.theme import plotly_layout


# ─────────────────────────────────────────────────────────────────────────────
# RACE CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def lap_time_distribution(df: pd.DataFrame, race: str, title: str = "") -> go.Figure:
    """Violin/box chart of lap time distribution per driver for a race."""
    fig = go.Figure()
    drivers = sorted(df["Driver"].unique())
    for driver in drivers:
        d_laps = df[df["Driver"] == driver]["LapTime"].dropna()
        fig.add_trace(go.Box(
            y=d_laps,
            name=driver,
            boxpoints="outliers",
            marker=dict(size=3, color=THEME_GOLD),
            line=dict(color=THEME_GOLD, width=1),
            fillcolor="rgba(212,175,55,0.1)",
        ))
    fig.update_layout(
        **plotly_layout(
            title=title or f"Lap Time Distribution — {race}",
            xaxis_title="Driver",
            yaxis_title="Lap Time (s)",
            showlegend=False,
            height=450,
        )
    )
    return fig


def race_pace_battle(
    df: pd.DataFrame,
    drivers: List[str],
    race: str,
    rolling: int = 3,
) -> go.Figure:
    """Multi-driver lap-by-lap pace comparison chart with optional rolling average."""
    COLORS = [THEME_GOLD, "#FF4444", "#44AAFF", "#44FF88", "#FF44AA", "#FFAA44",
              "#AA44FF", "#FF8844", "#44FFFF", "#FFFF44"]
    fig = go.Figure()
    for i, driver in enumerate(drivers):
        d_laps = df[(df["Driver"] == driver) & df["LapTime"].notna()].sort_values("LapNumber")
        color = COLORS[i % len(COLORS)]
        # Raw laps (faint)
        fig.add_trace(go.Scatter(
            x=d_laps["LapNumber"],
            y=d_laps["LapTime"],
            mode="lines",
            name=f"{driver} (raw)",
            line=dict(color=color, width=1, dash="dot"),
            opacity=0.3,
            showlegend=False,
        ))
        # Rolling average
        if rolling > 1 and len(d_laps) >= rolling:
            d_laps = d_laps.copy()
            d_laps["rolling"] = d_laps["LapTime"].rolling(rolling, center=True).mean()
            fig.add_trace(go.Scatter(
                x=d_laps["LapNumber"],
                y=d_laps["rolling"],
                mode="lines",
                name=driver,
                line=dict(color=color, width=2.5),
                hovertemplate=f"<b>{driver}</b><br>Lap %{{x}}<br>%{{y:.3f}}s<extra></extra>",
            ))
    fig.update_layout(
        **plotly_layout(
            title=f"Race Pace Battle — {race}",
            xaxis_title="Lap Number",
            yaxis_title="Lap Time (s)",
            height=480,
        )
    )
    return fig


def lap_position_chart(
    df: pd.DataFrame,
    drivers: Optional[List[str]] = None,
    race: str = "",
) -> go.Figure:
    """
    Position progression line chart across all race laps.
    Y-axis inverted so P1 is at the top.
    """
    COLORS = [
        THEME_GOLD, "#E8002D", "#39B54A", "#0090FF", "#FF8700",
        "#B138DD", "#00D2BE", "#6CD3BF", "#900000", "#FFFFFF",
        "#FF8080", "#80FF80", "#8080FF", "#FFFF80", "#FF80FF",
        "#80FFFF", "#FFA500", "#DA70D6", "#98FB98", "#AFEEEE",
    ]
    fig = go.Figure()

    all_drivers = sorted(df["Driver"].dropna().unique())
    selected = drivers if drivers else all_drivers

    for i, driver in enumerate(selected):
        d_df = df[df["Driver"] == driver].dropna(subset=["Position"]).sort_values("LapNumber")
        if len(d_df) == 0:
            continue
        color = COLORS[i % len(COLORS)]
        fig.add_trace(go.Scatter(
            x=d_df["LapNumber"],
            y=d_df["Position"],
            mode="lines+markers",
            name=driver,
            line=dict(color=color, width=2.2),
            marker=dict(size=4),
            hovertemplate=f"<b>{driver}</b><br>Lap %{{x}}<br>Position: P%{{y}}<extra></extra>",
        ))

    layout = plotly_layout(
        title=f"Position Progression — {race}" if race else "Position Progression",
        xaxis_title="Lap Number",
        yaxis_title="Track Position (P1 top)",
        height=520,
    )
    layout["yaxis"]["autorange"] = "reversed"
    layout["yaxis"]["dtick"] = 1
    fig.update_layout(**layout)
    return fig


def teammate_battle_chart(teammate_df: pd.DataFrame, race: str = "") -> go.Figure:
    """
    Intra-team pace delta horizontal bar chart for a single race.
    """
    if teammate_df.empty:
        return go.Figure()

    labels = []
    deltas = []
    colors = []
    hover_texts = []

    for _, row in teammate_df.iterrows():
        t = row.get("team", "")
        d1 = row.get("driver_1", "")
        d2 = row.get("driver_2", "")
        delta = row.get("pace_delta", 0.0)
        
        labels.append(f"{t}: {d1} vs {d2}")
        deltas.append(delta)
        if delta < 0:
            colors.append(THEME_GOLD)
            hover_texts.append(f"{d1} faster by {abs(delta):.3f}s/lap")
        else:
            colors.append("#44AAFF")
            hover_texts.append(f"{d2} faster by {abs(delta):.3f}s/lap")

    fig = go.Figure(go.Bar(
        x=deltas,
        y=labels,
        orientation="h",
        marker=dict(color=colors),
        hovertemplate="%{text}<extra></extra>",
        text=hover_texts,
    ))

    fig.update_layout(
        **plotly_layout(
            title=f"Teammate Representative Pace Delta — {race}",
            xaxis_title="Pace Delta (Seconds / Lap) [← Left: Driver 1 Faster | Right: Driver 2 Faster →]",
            yaxis_title="",
            height=max(350, len(labels) * 35),
        )
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# DRIVER EVOLUTION & RADAR CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def driver_radar_chart(
    driver_name: str,
    metrics: Dict[str, float],
    compare_driver: Optional[str] = None,
    compare_metrics: Optional[Dict[str, float]] = None,
) -> go.Figure:
    """
    Polar radar chart showing normalized 0-100 skill ratings.
    """
    categories = list(metrics.keys())
    values = list(metrics.values())
    categories.append(categories[0])
    values.append(values[0])

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill="toself",
        name=driver_name,
        line=dict(color=THEME_GOLD, width=2.5),
        fillcolor="rgba(212,175,55,0.25)",
    ))

    if compare_driver and compare_metrics:
        comp_values = list(compare_metrics.values())
        comp_values.append(comp_values[0])
        fig.add_trace(go.Scatterpolar(
            r=comp_values,
            theta=categories,
            fill="toself",
            name=compare_driver,
            line=dict(color="#44AAFF", width=2.5),
            fillcolor="rgba(68,170,255,0.2)",
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color=THEME_GREY, size=10),
                gridcolor="#333",
            ),
            angularaxis=dict(
                tickfont=dict(color=THEME_WHITE, size=12, family="Inter"),
                gridcolor="#333",
            ),
            bgcolor="#161616",
        ),
        paper_bgcolor="#161616",
        font=dict(color=THEME_WHITE),
        title=dict(
            text=f"Performance DNA Radar — {driver_name}" + (f" vs {compare_driver}" if compare_driver else ""),
            font=dict(color=THEME_GOLD, size=15),
        ),
        height=450,
        margin=dict(l=50, r=50, t=50, b=50),
    )
    return fig


def driver_form_momentum_chart(evolution_df: pd.DataFrame, driver: str) -> go.Figure:
    """
    Plots finishing position alongside 3-race rolling momentum curve.
    """
    d = evolution_df[evolution_df["driver"] == driver].sort_values("race_round")
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=d["race"],
        y=d["finishing_position"],
        mode="markers",
        name="Race Finish",
        marker=dict(size=9, color="#888", symbol="diamond"),
        hovertemplate="<b>%{x}</b><br>Finish: P%{y}<extra></extra>",
    ))

    if "rolling_3_finish" in d.columns:
        fig.add_trace(go.Scatter(
            x=d["race"],
            y=d["rolling_3_finish"],
            mode="lines+markers",
            name="3-Race Form Momentum",
            line=dict(color=THEME_GOLD, width=3.0),
            marker=dict(size=6, color=THEME_GOLD),
            hovertemplate="<b>%{x}</b><br>3-Race Avg: P%{y:.1f}<extra></extra>",
        ))

    layout = plotly_layout(
        title=f"Form Momentum Arc — {driver} (3-Race Rolling Average)",
        xaxis_title="Grand Prix",
        yaxis_title="Finishing Position (P1 top)",
        height=420,
        xaxis=dict(tickangle=-30),
    )
    layout["yaxis"]["autorange"] = "reversed"
    layout["yaxis"]["dtick"] = 2
    fig.update_layout(**layout)
    return fig


def relative_pace_evolution_chart(evolution_df: pd.DataFrame, drivers: List[str]) -> go.Figure:
    """
    Plots relative pace delta to grid median (seconds) over all 24 rounds.
    Negative values = faster than grid median.
    """
    COLORS = [THEME_GOLD, "#FF4444", "#44AAFF", "#44FF88", "#FF44AA", "#FFAA44",
              "#AA44FF", "#FF8844", "#44FFFF", "#FFFF44"]
    fig = go.Figure()

    fig.add_hline(
        y=0.0, line_dash="dash", line_color=THEME_GREY,
        annotation_text="Grid Median Pace", annotation_position="top right"
    )

    for i, driver in enumerate(drivers):
        d = evolution_df[evolution_df["driver"] == driver].sort_values("race_round")
        if len(d) == 0 or "relative_pace_to_median" not in d.columns:
            continue
        color = COLORS[i % len(COLORS)]
        fig.add_trace(go.Scatter(
            x=d["race"],
            y=d["relative_pace_to_median"],
            mode="lines+markers",
            name=driver,
            line=dict(color=color, width=2.2),
            marker=dict(size=6, color=color),
            hovertemplate=f"<b>{driver}</b><br>%{{x}}<br>Delta to Grid: %{{y:+.3f}}s<extra></extra>",
        ))

    layout = plotly_layout(
        title="Relative Pace Index across 2025 Season (Delta to Grid Median)",
        xaxis_title="Grand Prix",
        yaxis_title="Pace Delta to Grid Median (s) [Negative = Faster]",
        height=460,
        xaxis=dict(tickangle=-30),
    )
    layout["yaxis"]["autorange"] = "reversed"
    fig.update_layout(**layout)
    return fig


def teammate_gap_progression_chart(teammate_df: pd.DataFrame, team: str) -> go.Figure:
    """
    Plots how the intra-team pace delta developed round-by-round across the season.
    """
    tm_team = teammate_df[teammate_df["team"] == team].sort_values("race_round")
    if tm_team.empty:
        return go.Figure()

    d1 = tm_team["driver"].iloc[0]
    d2 = tm_team["teammate"].iloc[0]
    d1_rows = tm_team[tm_team["driver"] == d1]

    fig = go.Figure()
    fig.add_hline(y=0.0, line_dash="dash", line_color="#444")

    fig.add_trace(go.Scatter(
        x=d1_rows["race"],
        y=d1_rows["pace_delta"],
        mode="lines+markers",
        name=f"{d1} vs {d2}",
        line=dict(color=THEME_GOLD, width=2.5),
        marker=dict(size=7, color=THEME_GOLD),
        hovertemplate=f"<b>%{{x}}</b><br>Delta ({d1} - {d2}): %{{y:+.3f}}s<extra></extra>",
    ))

    fig.update_layout(
        **plotly_layout(
            title=f"Intra-Team Pace Delta Progression — {team} ({d1} vs {d2})",
            xaxis_title="Grand Prix",
            yaxis_title=f"Pace Delta (s) [Negative: {d1} Faster | Positive: {d2} Faster]",
            height=400,
            xaxis=dict(tickangle=-30),
        )
    )
    return fig


def driver_trajectory(
    evolution_df: pd.DataFrame,
    driver: str,
    metric: str = "rep_pace",
    metric_label: str = "Representative Pace (s)",
) -> go.Figure:
    """Single-driver season trajectory chart."""
    d = evolution_df[evolution_df["driver"] == driver].sort_values("race_round")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d["race"],
        y=d[metric],
        mode="lines+markers",
        name=driver,
        line=dict(color=THEME_GOLD, width=2.5),
        marker=dict(size=8, color=THEME_GOLD, symbol="circle"),
        hovertemplate=f"<b>{driver}</b><br>%{{x}}<br>{metric_label}: %{{y:.3f}}<extra></extra>",
    ))
    fig.update_layout(
        **plotly_layout(
            title=f"{driver} — Season Trajectory ({metric_label})",
            xaxis_title="Race",
            yaxis_title=metric_label,
            height=420,
            xaxis=dict(tickangle=-30),
        )
    )
    return fig


def multi_driver_trajectory(
    evolution_df: pd.DataFrame,
    drivers: List[str],
    metric: str = "finishing_position",
    metric_label: str = "Finishing Position",
    invert_y: bool = False,
) -> go.Figure:
    """Compare multiple drivers across the season for a given metric."""
    COLORS = [THEME_GOLD, "#FF4444", "#44AAFF", "#44FF88", "#FF44AA", "#FFAA44",
              "#AA44FF", "#FF8844", "#44FFFF", "#FFFF44"]
    fig = go.Figure()
    for i, driver in enumerate(drivers):
        d = evolution_df[evolution_df["driver"] == driver].sort_values("race_round")
        if len(d) == 0 or metric not in d.columns:
            continue
        color = COLORS[i % len(COLORS)]
        fig.add_trace(go.Scatter(
            x=d["race"],
            y=d[metric],
            mode="lines+markers",
            name=driver,
            line=dict(color=color, width=2),
            marker=dict(size=7, color=color),
            hovertemplate=f"<b>{driver}</b><br>%{{x}}<br>{metric_label}: %{{y}}<extra></extra>",
        ))
    layout = plotly_layout(
        title=f"Driver Comparison — {metric_label}",
        xaxis_title="Race",
        yaxis_title=metric_label,
        height=480,
        xaxis=dict(tickangle=-30),
    )
    if invert_y:
        layout["yaxis"]["autorange"] = "reversed"
    fig.update_layout(**layout)
    return fig


def performance_heatmap(evolution_df: pd.DataFrame, metric: str = "finishing_position") -> go.Figure:
    """Driver × Race performance heatmap."""
    if "race_round" in evolution_df.columns:
        ordered_races = (
            evolution_df[["race", "race_round"]].drop_duplicates()
            .sort_values("race_round")["race"].tolist()
        )
    else:
        ordered_races = sorted(evolution_df["race"].unique())

    pivot = evolution_df.pivot_table(
        index="driver", columns="race", values=metric, aggfunc="first"
    )
    pivot = pivot[ordered_races] if all(r in pivot.columns for r in ordered_races) else pivot

    colorscale = "RdYlGn_r" if "position" in metric.lower() else "Viridis"

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=colorscale,
        hovertemplate="<b>%{y}</b><br>%{x}<br>Value: %{z}<extra></extra>",
        colorbar=dict(
            title=metric,
            tickfont=dict(color=THEME_GREY),
            title_font=dict(color=THEME_GREY),
        ),
    ))
    fig.update_layout(
        **plotly_layout(
            title=f"Season Performance Heatmap — {metric}",
            xaxis_title="Grand Prix",
            yaxis_title="Driver",
            height=620,
            xaxis=dict(tickangle=-45),
        )
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# CHAMPIONSHIP CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def championship_progression(
    progression_df: pd.DataFrame,
    top_n: int = 10,
) -> go.Figure:
    """Race-by-race cumulative points chart for top N drivers."""
    COLORS = [THEME_GOLD, "#FF4444", "#44AAFF", "#44FF88", "#FF44AA",
              "#FFAA44", "#AA44FF", "#FF8844", "#44FFFF", "#FFFF44"]
    if "cumulative_points_estimate" in progression_df.columns:
        top_drivers = (
            progression_df.groupby("driver")["cumulative_points_estimate"]
            .max().nlargest(top_n).index.tolist()
        )
        y_col = "cumulative_points_estimate"
    else:
        return go.Figure()

    fig = go.Figure()
    for i, driver in enumerate(top_drivers):
        d = progression_df[progression_df["driver"] == driver].sort_values("race_round")
        fig.add_trace(go.Scatter(
            x=d["race"],
            y=d[y_col],
            mode="lines+markers",
            name=driver,
            line=dict(color=COLORS[i % len(COLORS)], width=2.5),
            marker=dict(size=6),
            hovertemplate=f"<b>{driver}</b><br>%{{x}}<br>Points: %{{y}}<extra></extra>",
        ))
    fig.update_layout(
        **plotly_layout(
            title="Championship Progression (Points Estimate)",
            xaxis_title="Race",
            yaxis_title="Cumulative Points (Estimate)",
            height=500,
            xaxis=dict(tickangle=-30),
        )
    )
    return fig


def championship_bar(standings_df: pd.DataFrame, title: str = "2025 Championship Standings") -> go.Figure:
    """Horizontal bar chart of championship points."""
    df = standings_df.sort_values("rank") if "rank" in standings_df.columns else standings_df

    driver_col = "driver" if "driver" in df.columns else "team"
    points_col = "points" if "points" in df.columns else "points_estimate"

    fig = go.Figure(go.Bar(
        x=df[points_col],
        y=df[driver_col],
        orientation="h",
        marker=dict(
            color=df[points_col],
            colorscale=[[0, "#222"], [1, THEME_GOLD]],
        ),
        hovertemplate="<b>%{y}</b><br>Points: %{x}<extra></extra>",
    ))
    fig.update_layout(
        **plotly_layout(
            title=title,
            xaxis_title="Points",
            yaxis_title="",
            height=max(350, len(df) * 30),
            yaxis=dict(autorange="reversed"),
        )
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# TYRE & STRATEGY CHARTS (PHASE 5 ENHANCED)
# ─────────────────────────────────────────────────────────────────────────────

def tyre_degradation_curve(
    stint_laps: pd.DataFrame,
    driver: str,
    stint: int,
    compound: str,
    cliff_lap: Optional[int] = None
) -> go.Figure:
    """Lap-by-lap pace within a single stint with degradation trend and optional cliff marker."""
    valid = stint_laps[stint_laps["LapTime"].notna()].sort_values("LapNumber")
    color = COMPOUND_COLORS.get(compound, THEME_GREY)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=valid["LapNumber"],
        y=valid["LapTime"],
        mode="lines+markers",
        name=f"Stint {stint} ({compound})",
        line=dict(color=color, width=2.5),
        marker=dict(size=7, color=color),
        hovertemplate="Lap %{x}<br>%{y:.3f}s<extra></extra>",
    ))
    if len(valid) >= 4:
        z = np.polyfit(valid["LapNumber"], valid["LapTime"], 1)
        p = np.poly1d(z)
        slope = z[0]
        fig.add_trace(go.Scatter(
            x=valid["LapNumber"],
            y=p(valid["LapNumber"]),
            mode="lines",
            name=f"Degradation ({slope:+.3f}s/lap)",
            line=dict(color=THEME_GREY, width=1.5, dash="dash"),
        ))

    if cliff_lap is not None:
        fig.add_vline(
            x=cliff_lap, line_dash="dot", line_color=THEME_RED,
            annotation_text="Tyre Cliff ⚠️", annotation_position="top left"
        )

    fig.update_layout(
        **plotly_layout(
            title=f"{driver} — Stint {stint} Degradation ({compound})",
            xaxis_title="Lap Number",
            yaxis_title="Lap Time (s)",
            height=380,
        )
    )
    return fig


def compound_degradation_comparison_chart(matrix_df: pd.DataFrame) -> go.Figure:
    """
    Bar chart comparing average degradation slopes and stint longevity by compound.
    """
    if matrix_df.empty:
        return go.Figure()

    fig = go.Figure()
    for _, row in matrix_df.iterrows():
        comp = row["compound"]
        color = COMPOUND_COLORS.get(comp, THEME_GREY)
        fig.add_trace(go.Bar(
            x=[comp],
            y=[row.get("avg_degradation_slope", 0.0)],
            name=comp,
            marker=dict(color=color),
            hovertemplate=f"<b>{comp}</b><br>Degradation: %{{y:.4f}} s/lap<br>Avg Stint: {row.get('avg_stint_length', 0):.1f} laps<extra></extra>",
        ))

    fig.update_layout(
        **plotly_layout(
            title="Compound Degradation Rate (Seconds Lost / Lap)",
            xaxis_title="Tyre Compound",
            yaxis_title="Degradation Slope (s/lap)",
            height=380,
            showlegend=False,
        )
    )
    return fig


def strategy_distribution_donut(strategy_df: pd.DataFrame, race: str) -> go.Figure:
    """
    Donut chart of strategy type splits (1-Stop vs 2-Stop etc.) across the grid.
    """
    race_strats = strategy_df[strategy_df["race"] == race] if "race" in strategy_df.columns else strategy_df
    if race_strats.empty or "strategy_type" not in race_strats.columns:
        return go.Figure()

    counts = race_strats["strategy_type"].value_counts()
    fig = go.Figure(data=[go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.55,
        marker=dict(colors=[THEME_GOLD, "#44AAFF", "#FF4444", "#39B54A"]),
        hovertemplate="<b>%{label}</b><br>%{value} Drivers (%{percent})<extra></extra>",
    )])

    fig.update_layout(
        paper_bgcolor="#161616",
        font=dict(color=THEME_WHITE),
        title=dict(text=f"Strategy Distribution — {race}", font=dict(color=THEME_GOLD, size=14)),
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def undercut_battles_chart(battles_df: pd.DataFrame, race: str) -> go.Figure:
    """
    Visualizes tactical undercut & overcut battles during pit windows.
    """
    if battles_df.empty:
        return go.Figure()

    labels = [f"{r['attacker']} vs {r['defender']}" for _, r in battles_df.iterrows()]
    gaps = battles_df["gap_laps"].tolist()
    colors = [THEME_GREEN if r["successful"] else THEME_RED for _, r in battles_df.iterrows()]

    fig = go.Figure(go.Bar(
        x=gaps,
        y=labels,
        orientation="h",
        marker=dict(color=colors),
        hovertemplate="<b>%{y}</b><br>Pit Stop Gap: %{x} laps<extra></extra>",
    ))

    fig.update_layout(
        **plotly_layout(
            title=f"Pit Window Undercut Attempts — {race} (Green = Success | Red = Defended)",
            xaxis_title="Lap Differential at Pit Entry",
            yaxis_title="",
            height=max(300, len(labels) * 35),
        )
    )
    return fig


def strategy_gantt(strategy_df: pd.DataFrame, race: str) -> go.Figure:
    """Horizontal gantt-style strategy timeline per driver."""
    race_strats = strategy_df[strategy_df["race"] == race] if "race" in strategy_df.columns else strategy_df
    fig = go.Figure()
    drivers = race_strats["driver"].unique() if "driver" in race_strats.columns else []
    for i, driver in enumerate(sorted(drivers)):
        row = race_strats[race_strats["driver"] == driver]
        if len(row) == 0:
            continue
        row = row.iloc[0]
        seq = row.get("compound_sequence", [])
        lengths = row.get("stint_lengths", [])
        if isinstance(seq, str):
            import ast
            try:
                seq = ast.literal_eval(seq)
                lengths = ast.literal_eval(str(lengths))
            except Exception:
                seq, lengths = [], []
        start = 1
        for j, (compound, length) in enumerate(zip(seq, lengths)):
            color = COMPOUND_COLORS.get(compound, THEME_GREY)
            fig.add_trace(go.Bar(
                x=[length],
                y=[driver],
                orientation="h",
                base=start - 1,
                name=compound if i == 0 else None,
                marker=dict(color=color, line=dict(color="#0a0a0a", width=1)),
                hovertemplate=f"<b>{driver}</b><br>Stint {j+1}: {compound}<br>Laps {start}–{start+length-1}<extra></extra>",
                showlegend=(i == 0),
            ))
            start += length
    fig.update_layout(
        **plotly_layout(
            title=f"Race Strategy Timeline — {race}",
            xaxis_title="Lap Number",
            yaxis_title="Driver",
            barmode="stack",
            height=520,
        )
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 6: RACE REPLAY & CONTEXT CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def race_neutralization_chart(neut_df: pd.DataFrame, race: str) -> go.Figure:
    """
    Visualizes whole-grid median pace evolution across laps, highlighting SC and VSC zones.
    """
    if neut_df.empty or "LapNumber" not in neut_df.columns:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=neut_df["LapNumber"],
        y=neut_df["median_time"],
        mode="lines+markers",
        name="Median Lap Pace",
        line=dict(color=THEME_GOLD, width=2.5),
        marker=dict(size=4),
        hovertemplate="Lap %{x}<br>Median Pace: %{y:.3f}s<extra></extra>",
    ))

    # Highlight SC / VSC bands
    for _, row in neut_df.iterrows():
        lap = int(row["LapNumber"])
        status = row.get("status", "")
        if "SAFETY CAR" in status:
            fig.add_vrect(x0=lap-0.5, x1=lap+0.5, fillcolor="#FFF200", opacity=0.25, line_width=0)
        elif "VSC" in status:
            fig.add_vrect(x0=lap-0.5, x1=lap+0.5, fillcolor="#FF8844", opacity=0.2, line_width=0)

    fig.update_layout(
        **plotly_layout(
            title=f"Race Pace Rhythm & Neutralizations — {race} (Yellow = SC / VSC)",
            xaxis_title="Lap Number",
            yaxis_title="Median Lap Time (s)",
            height=380,
        )
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 7: TELEMETRY LAB CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def telemetry_speed_trace_chart(
    d1_telemetry: pd.DataFrame,
    d2_telemetry: Optional[pd.DataFrame] = None,
) -> go.Figure:
    """
    Overlays speed traces across track distance for one or two drivers.
    """
    if d1_telemetry.empty:
        return go.Figure()

    fig = go.Figure()
    d1_name = d1_telemetry["driver"].iloc[0] if "driver" in d1_telemetry.columns else "Driver 1"

    fig.add_trace(go.Scatter(
        x=d1_telemetry["distance_m"],
        y=d1_telemetry["speed_kmh"],
        mode="lines",
        name=f"{d1_name} ({d1_telemetry['lap_time'].iloc[0]:.3f}s)",
        line=dict(color=THEME_GOLD, width=2.5),
        hovertemplate=f"<b>{d1_name}</b><br>Distance: %{{x}}m<br>Speed: %{{y:.1f}} km/h<extra></extra>",
    ))

    if d2_telemetry is not None and not d2_telemetry.empty:
        d2_name = d2_telemetry["driver"].iloc[0] if "driver" in d2_telemetry.columns else "Driver 2"
        fig.add_trace(go.Scatter(
            x=d2_telemetry["distance_m"],
            y=d2_telemetry["speed_kmh"],
            mode="lines",
            name=f"{d2_name} ({d2_telemetry['lap_time'].iloc[0]:.3f}s)",
            line=dict(color="#44AAFF", width=2.2, dash="dash"),
            hovertemplate=f"<b>{d2_name}</b><br>Distance: %{{x}}m<br>Speed: %{{y:.1f}} km/h<extra></extra>",
        ))

    fig.update_layout(
        **plotly_layout(
            title="Telemetry Speed Trace Overlay (km/h vs Distance)",
            xaxis_title="Track Distance (m)",
            yaxis_title="Speed (km/h)",
            height=420,
        )
    )
    return fig


def telemetry_multichannel_chart(
    d1_telemetry: pd.DataFrame,
    d2_telemetry: Optional[pd.DataFrame] = None,
) -> go.Figure:
    """
    Displays multi-channel driver telemetry (Throttle %, Brake %, Gear).
    """
    from plotly.subplots import make_subplots
    if d1_telemetry.empty:
        return go.Figure()

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
        subplot_titles=("Throttle Application (%)", "Brake Pressure (%)", "Gear Selection")
    )

    d1 = d1_telemetry["driver"].iloc[0] if "driver" in d1_telemetry.columns else "Driver 1"

    # Throttle
    fig.add_trace(go.Scatter(
        x=d1_telemetry["distance_m"], y=d1_telemetry["throttle_pct"],
        mode="lines", name=f"{d1} Throttle", line=dict(color=THEME_GREEN, width=1.8),
    ), row=1, col=1)

    # Brake
    fig.add_trace(go.Scatter(
        x=d1_telemetry["distance_m"], y=d1_telemetry["brake_pct"],
        mode="lines", name=f"{d1} Brake", line=dict(color=THEME_RED, width=1.8),
    ), row=2, col=1)

    # Gear
    fig.add_trace(go.Scatter(
        x=d1_telemetry["distance_m"], y=d1_telemetry["gear"],
        mode="lines", name=f"{d1} Gear", line=dict(color=THEME_GOLD, width=1.8),
    ), row=3, col=1)

    if d2_telemetry is not None and not d2_telemetry.empty:
        d2 = d2_telemetry["driver"].iloc[0] if "driver" in d2_telemetry.columns else "Driver 2"
        fig.add_trace(go.Scatter(
            x=d2_telemetry["distance_m"], y=d2_telemetry["throttle_pct"],
            mode="lines", name=f"{d2} Throttle", line=dict(color="#88FFAA", width=1.5, dash="dot"),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=d2_telemetry["distance_m"], y=d2_telemetry["brake_pct"],
            mode="lines", name=f"{d2} Brake", line=dict(color="#FFAA88", width=1.5, dash="dot"),
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=d2_telemetry["distance_m"], y=d2_telemetry["gear"],
            mode="lines", name=f"{d2} Gear", line=dict(color="#44AAFF", width=1.5, dash="dot"),
        ), row=3, col=1)

    fig.update_layout(
        paper_bgcolor="#161616", plot_bgcolor="#111111",
        font=dict(color=THEME_WHITE), height=550,
        margin=dict(l=40, r=20, t=40, b=30), showlegend=True
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 7: ANOMALY CENTER CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def anomaly_scatter_chart(anomalies_df: pd.DataFrame, race: str) -> go.Figure:
    """
    Scatter plot showing detected anomalies by lap and deviation magnitude (Z-Score).
    """
    if anomalies_df.empty:
        return go.Figure()

    r_anom = anomalies_df[anomalies_df["race"] == race] if "race" in anomalies_df.columns else anomalies_df
    if r_anom.empty:
        return go.Figure()

    color_map = {"CRITICAL": THEME_RED, "WARNING": THEME_ORANGE, "INFO": THEME_GOLD}
    colors = [color_map.get(s, THEME_GREY) for s in r_anom["severity"]]

    fig = go.Figure(go.Scatter(
        x=r_anom["lap"],
        y=r_anom["z_score"],
        mode="markers+text",
        text=r_anom["driver"],
        textposition="top center",
        marker=dict(size=11, color=colors, line=dict(color="#ffffff", width=1)),
        hovertemplate="<b>%{text}</b> (Lap %{x})<br>Z-Score: %{y:.1f}<extra></extra>",
    ))

    fig.update_layout(
        **plotly_layout(
            title=f"Statistical Anomaly Events — {race} (Lap vs Severity Z-Score)",
            xaxis_title="Lap Number",
            yaxis_title="Pace Anomaly Z-Score",
            height=380,
        )
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 8: TEAM INTELLIGENCE CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def team_development_trajectory_chart(
    trajectory_df: pd.DataFrame,
    selected_teams: Optional[List[str]] = None,
) -> go.Figure:
    """
    Traces in-season pace delta to grid median for selected constructors across 24 rounds.
    Inverted Y-axis (negative pace delta = faster than median = higher on chart).
    """
    if trajectory_df.empty:
        return go.Figure()

    fig = go.Figure()
    teams = selected_teams if selected_teams else sorted(trajectory_df["team"].unique().tolist())

    PALETTE = [THEME_GOLD, "#FF4444", "#44AAFF", "#44FF88", "#FF44AA",
               "#FFAA44", "#AA44FF", "#00E5FF", "#FFFF44", "#888888"]

    for i, team in enumerate(teams):
        t_data = trajectory_df[trajectory_df["team"] == team].sort_values("race_round")
        if t_data.empty:
            continue

        fig.add_trace(go.Scatter(
            x=t_data["race"],
            y=t_data["pace_delta_to_median"],
            mode="lines+markers",
            name=team,
            line=dict(color=PALETTE[i % len(PALETTE)], width=2.5),
            marker=dict(size=6),
            hovertemplate=f"<b>{team}</b><br>%{{x}}<br>Delta: %{{y:+.3f}}s<extra></extra>",
        ))

    fig.add_hline(y=0.0, line_dash="dash", line_color=THEME_GREY, annotation_text="Grid Median (0.0s)")

    fig.update_layout(
        **plotly_layout(
            title="Constructor Pace Development Trajectory (Pace Delta to Grid Median)",
            xaxis_title="Grand Prix",
            yaxis_title="Pace Delta to Median (s, Lower/Negative is Faster)",
            height=460,
            yaxis=dict(autorange="reversed"),
            xaxis=dict(tickangle=-30),
        )
    )
    return fig


def team_pit_efficiency_chart(pit_df: pd.DataFrame) -> go.Figure:
    """
    Bar chart of average pit stops per race and strategy execution by team.
    """
    if pit_df.empty:
        return go.Figure()

    fig = go.Figure(go.Bar(
        x=pit_df["team"],
        y=pit_df["avg_pit_stops_per_race"],
        marker=dict(color=THEME_GOLD),
        hovertemplate="<b>%{x}</b><br>Avg Pit Stops: %{y:.2f}<br>1-Stop Rate: %{customdata:.1f}%<extra></extra>",
        customdata=pit_df["one_stop_pct"],
    ))

    fig.update_layout(
        **plotly_layout(
            title="Pit Stop Execution Rate by Constructor (Avg Stops per Car)",
            xaxis_title="Constructor",
            yaxis_title="Avg Stops / Race",
            height=360,
            xaxis=dict(tickangle=-25),
        )
    )
    return fig


def race_simulation_probability_chart(sim_df: pd.DataFrame, race: str) -> go.Figure:
    """
    Horizontal stacked probability bar chart showing Win %, Podium %, and Points Finish % from Monte Carlo simulations.
    """
    if sim_df.empty:
        return go.Figure()

    top_drivers = sim_df.head(10).sort_values("win_probability_pct", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top_drivers["driver"],
        x=top_drivers["win_probability_pct"],
        name="Win % 🏆",
        orientation="h",
        marker=dict(color=THEME_GOLD),
        hovertemplate="<b>%{y}</b><br>Win Probability: %{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=top_drivers["driver"],
        x=top_drivers["podium_probability_pct"] - top_drivers["win_probability_pct"],
        name="Podium (P2-P3) % 🥈",
        orientation="h",
        marker=dict(color="#44AAFF"),
        hovertemplate="<b>%{y}</b><br>Podium Probability: %{customdata:.1f}%<extra></extra>",
        customdata=top_drivers["podium_probability_pct"],
    ))
    fig.add_trace(go.Bar(
        y=top_drivers["driver"],
        x=top_drivers["points_probability_pct"] - top_drivers["podium_probability_pct"],
        name="Points (P4-P10) % 📈",
        orientation="h",
        marker=dict(color=THEME_GREEN),
        hovertemplate="<b>%{y}</b><br>Points Probability: %{customdata:.1f}%<extra></extra>",
        customdata=top_drivers["points_probability_pct"],
    ))

    fig.update_layout(
        **plotly_layout(
            title=f"Monte Carlo Probabilistic Race Outcome (1,000 Iterations) — {race}",
            xaxis_title="Outcome Probability (%)",
            yaxis_title="Driver",
            barmode="stack",
            height=440,
        )
    )
    return fig


