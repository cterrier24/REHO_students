import re
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.lines import Line2D
import contextily as ctx
import osmnx as ox
import os
from typing import List, Optional, Tuple

# --- Consistent period order and colors (publication-ready) ---
from matplotlib import cm

def _get_period_order():
    return [
        "<1919","1919-1945","1946-1960","1961-1970","1971-1980",
        "1981-1990","1991-2000","2001-2010",">2010"
    ]

def _get_period_color_map():
    PERIOD_ORDER = _get_period_order()
    cmap = cm.get_cmap('OrRd')  # ColorBrewer, print-friendly
    vals = np.linspace(0.2, 0.9, len(PERIOD_ORDER))
    return {p: cmap(v) for p, v in zip(PERIOD_ORDER, vals)}


def _safe_float(x):
    try:
        return float(str(x).replace('%','').strip())
    except Exception:
        return float('-inf')

def pick_by_ratio(period_str, class_str, ratio_str):
    """Select period & class based on the largest ratio, but be robust to
    uneven token counts and missing ratios so we don't end up with 'Unknown'."""
    periods = [s.strip() for s in str(period_str).split('/') if str(s).strip() != ""]
    classes = [s.strip() for s in str(class_str).split('/') if str(s).strip() != ""]
    ratios  = [_safe_float(s) for s in str(ratio_str).split('/') if str(s).strip() != ""]

    # If class only has one value, use it regardless of ratios
    if len(classes) == 1:
        chosen_class = classes[0]
    else:
        # If ratios are missing/invalid, default to the first non-empty class
        if not ratios or all(r == float('-inf') for r in ratios):
            chosen_class = classes[0] if classes else "Unknown"
        else:
            # Pick index of max ratio, but clamp to available class tokens
            max_idx = max(range(len(ratios)), key=lambda i: ratios[i])
            max_idx = min(max_idx, len(classes) - 1) if classes else 0
            chosen_class = classes[max_idx] if classes else "Unknown"

    # Period selection mirrors class logic, but tolerate missing tokens
    if len(periods) == 1:
        chosen_period = periods[0]
    else:
        if not ratios or all(r == float('-inf') for r in ratios):
            chosen_period = periods[0] if periods else "Unknown"
        else:
            max_idx = max(range(len(ratios)), key=lambda i: ratios[i])
            max_idx = min(max_idx, len(periods) - 1) if periods else 0
            chosen_period = periods[max_idx] if periods else "Unknown"

    return chosen_period or "Unknown", chosen_class or "Unknown"

def plot_district(CSV_FILE, PERIM_FILE, filename, plot_class=False, basemap=False, ax=None, show_legend=True):
    df = pd.read_csv(CSV_FILE)
    df["geometry"] = df["geometry"].apply(lambda g: wkt.loads(g) if isinstance(g, str) else g)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=BUILDINGS_CRS)
    gdf = gdf[gdf.geometry.notnull() & ~gdf.geometry.is_empty & gdf.is_valid].copy()

    gdf[["period_sel", "class_sel"]] = gdf.apply(
        lambda r: pd.Series(pick_by_ratio(r.get("period", ""), r.get("class", ""), r.get("ratio", ""))),
        axis=1
    )

    PERIOD_ORDER = _get_period_order()
    period_color_map = _get_period_color_map()

    if plot_class == True:
        # ==== CLASS → MARKERS (unchanged) ====
        classes = sorted([c for c in gdf["class_sel"].dropna().unique() if str(c).strip() != ""])
        marker_cycle = ['o','s','^','D','P','X','v','<','>','h','*','8']
        while len(marker_cycle) < len(classes):
            marker_cycle += marker_cycle
        class_marker_map = {c: marker_cycle[i] for i, c in enumerate(classes)}

    # ==== LOAD + REPROJECT PERIMETER ====
    with open(PERIM_FILE, "r", encoding="utf-8") as f:
        perim_geom = wkt.loads(f.read().strip())
    perim_gdf = gpd.GeoDataFrame(geometry=[perim_geom], crs=PERIM_CRS).to_crs(BUILDINGS_CRS)

    # Choose plotting CRS; if basemap, reproject to Web Mercator (EPSG:3857)
    if basemap:
        gdf_plot = gdf.to_crs(epsg=3857)
        perim_plot = perim_gdf.to_crs(epsg=3857)
    else:
        gdf_plot = gdf
        perim_plot = perim_gdf


    # ==== PLOT ====
    created_fig = None
    if ax is None:
        created_fig, ax = plt.subplots(figsize=(10, 8))

    # Buildings polygons, colored by period (plot only those present)
    for p in PERIOD_ORDER:
        sub = gdf_plot[gdf_plot["period_sel"] == p]
        if not sub.empty:
            sub.plot(ax=ax, color=period_color_map[p], edgecolor="black", linewidth=0.4, zorder=2)

    if plot_class == True:
        # Class symbols on centroids (visible and on top)
        centroids = gdf_plot.copy()
        centroids["geometry"] = centroids.geometry.centroid
        for c in classes:
            sub = centroids[centroids["class_sel"] == c]
            if not sub.empty:
                sub.plot(
                    ax=ax,
                    marker=class_marker_map[c],
                    facecolor="white",
                    edgecolor="k",
                    linewidth=1,
                    markersize=25,
                    zorder=4
                )

    # Perimeter outline (on top of fills, below markers)
    perim_plot.boundary.plot(ax=ax, color="black", linewidth=1.0, zorder=3)
    if basemap:
        #ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.PositronNoLabels)

        xb, yb = (0.0, 0.0)
        wb, hb = (1, 0.05)
        ax.add_patch(
            Rectangle((xb, yb), wb, hb,
                      transform=ax.transAxes,
                      facecolor='white', edgecolor='white', linewidth=0.1,
                      alpha=1, zorder=12)
        )

    # ==== LEGENDS ====
    # Period legend shows ALL bins, even if absent in this district
    period_handles = [Patch(facecolor=period_color_map[p], edgecolor="black", label=p) for p in PERIOD_ORDER]
    if show_legend:
        leg1 = ax.legend(handles=period_handles, title="Period", loc="upper left")
        ax.add_artist(leg1)
        if plot_class == True:
            class_handles  = [Line2D([0],[0], marker=class_marker_map[c], linestyle="None",
                                     markerfacecolor="white", markeredgecolor="k", markersize=10, label=c)
                              for c in classes]
            ax.legend(handles=class_handles, title="Class", loc="upper right")

    #ax.set_title(filename)
    ax.set_axis_off()
    if created_fig is not None:
        plt.tight_layout()
        plt.savefig(f"../plots/{filename}.pdf", format="pdf", dpi=300)

def plot_geneva_overview_top_with_district_subplots(
    DISTRICT_CSV_FILES: List[str],
    DISTRICT_PERIM_FILES: List[str],
    DISTRICT_LABELS: Optional[List[str]] = None,
    filename: str = "geneva_overview_top_with_subplots",
    basemap: bool = True,
    overview_zoom_out: float = 0.35,
    basemap_provider=None,
    white_box: bool = True,
    white_box_xy: Tuple = (0.0, 0.0),
    white_box_wh: Tuple = (1, 0.05),
    white_box_alpha: float = 1,
):
    """
    Layout: one big Geneva overview on top; three zoomed-in district subplots below (one row).
    Uses plot_district() to render each district subplot.
    """
    PERIOD_ORDER = _get_period_order()
    period_color_map = _get_period_color_map()

    if basemap_provider is None:
        #basemap_provider = ctx.providers.CartoDB.Positron
        basemap_provider = ctx.providers.OpenStreetMap.Mapnik
    # Read district perimeters for the overview extent and plotting
    district_geoms = []
    for p in DISTRICT_PERIM_FILES:
        with open(p, "r") as f:
            district_geoms.append(wkt.loads(f.read().strip()))
    districts_gdf = gpd.GeoDataFrame(geometry=district_geoms, crs=PERIM_CRS).to_crs(BUILDINGS_CRS)

    # Labels
    import os as _os
    if DISTRICT_LABELS is None:
        DISTRICT_LABELS = [_os.path.splitext(_os.path.basename(p))[0] for p in DISTRICT_PERIM_FILES]

    # CRS for plotting in overview (Web Mercator if basemap)
    if basemap:
        districts_plot = districts_gdf.to_crs(epsg=3857)
    else:
        districts_plot = districts_gdf

    # Figure layout: 2 rows, top spans all 3 columns, bottom has 3 columns
    fig = plt.figure(figsize=(14, 12))
    gs = fig.add_gridspec(nrows=2, ncols=3, height_ratios=[1.4, 1.0], wspace=0.01, hspace=0.01)

    # Top overview axis spans all columns
    ax_over = fig.add_subplot(gs[0, :])

    fig.patch.set_facecolor('white')
    for spine in ax_over.spines.values():
        spine.set_visible(False)

    # Bottom row: three subplots
    ax_subs = [fig.add_subplot(gs[1, i]) for i in range(3)]

    # --- Overview plotting (highlight all districts) ---
    highlight_face = "#FFEB3B"  # bright, luminous yellow
    districts_plot.plot(
        ax=ax_over,
        facecolor=highlight_face,
        edgecolor="#F57F17",
        linewidth=1.6,
        alpha=0.70,
        zorder=4,
    )
    # Zoom out around all districts
    x_min, y_min, x_max, y_max = districts_plot.total_bounds
    mx = (x_max - x_min) * overview_zoom_out
    my = (y_max - y_min) * overview_zoom_out
    ax_over.set_xlim(x_min - mx, x_max + mx)
    ax_over.set_ylim(y_min - my, y_max + my)

    if basemap:
        ctx.add_basemap(ax_over, source=basemap_provider, alpha = 0.7)
        # Optional white box for notes/legend in overview (axis coordinates)
        if white_box:
            xb, yb = white_box_xy
            wb, hb = white_box_wh
            ax_over.add_patch(
                Rectangle((xb, yb), wb, hb,
                          transform=ax_over.transAxes,
                          facecolor='white', edgecolor='white', linewidth=0.1,
                          alpha=white_box_alpha, zorder=12)
            )

    # Optional outside labels with leader lines on the overview
    tb_xmin, tb_ymin, tb_xmax, tb_ymax = districts_plot.total_bounds
    global_dx = (tb_xmax - tb_xmin) * 0.05
    for geom, label in zip(districts_plot.geometry, DISTRICT_LABELS):
        anchor = geom.representative_point()
        a_x, a_y = anchor.x, anchor.y
        gxmin, gymin, gxmax, gymax = geom.bounds
        x_text = gxmax + global_dx
        y_text = (gymin + gymax) / 2.0
        ax_over.annotate(
            label,
            xy=(a_x, a_y),
            xytext=(x_text, y_text),
            ha="left", va="center", fontsize=13, color="#444444",
            arrowprops=dict(arrowstyle="-", lw=1),
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none"),
            zorder=3,
        )
    ax_over.set_axis_off()

    # --- Bottom subplots using plot_district() ---
    for ax, csv_path, perim_path, label in zip(ax_subs, DISTRICT_CSV_FILES, DISTRICT_PERIM_FILES, DISTRICT_LABELS):
        # Use plot_district to render into the provided axes; no legends and no saving
        plot_district(
            CSV_FILE=csv_path,
            PERIM_FILE=perim_path,
            filename=label,
            plot_class=False,
            basemap=basemap,
            ax=ax,
            show_legend=False,
        )
        # Set title below the subplot
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_facecolor('white')
        ax.set_title(label, fontsize=9, y=-0.05)

    # --- Adjust y-limits to crop 5% from the bottom for all axes (overview and subplots) ---
    def add_bottom_5pct(ax):
        ymin, ymax = ax.get_ylim()
        new_ymin = ymin - (ymax - ymin) * 0.05
        ax.set_ylim(new_ymin, ymax)
    add_bottom_5pct(ax_over)
    for ax in ax_subs:
        add_bottom_5pct(ax)
    # --- Shared legend for construction years (periods) below the subplots ---
    period_handles = [Patch(facecolor=period_color_map[p], edgecolor='black', label=p) for p in PERIOD_ORDER]
    leg = fig.legend(
        handles=period_handles,
        title="Construction Year",
        loc="lower center",
        ncol=len(PERIOD_ORDER),
        bbox_to_anchor=(0.5, 0.03),
        frameon=False,
        handlelength=1.8, handleheight=0.8, columnspacing=0.8, borderaxespad=0.0,
    )
    plt.setp(leg.get_title(), fontsize=10)
    for text in leg.get_texts():
        text.set_fontsize(10)

    # Save combined figure
    plt.tight_layout(rect=[0, 0.06, 1, 1])
    plt.savefig(f"../plots/{filename}.pdf", format="pdf", dpi=400, bbox_inches="tight")

if __name__ == "__main__":

    # ==== INPUTS ====
    BUILDINGS_CRS = "EPSG:2056"  # buildings already in LV95
    PERIM_CRS = "EPSG:4326"  # perimeter WKT is lon/lat

    cases = [
        "Center",
        "Villa",
        "Rural",
    ]

    plot_geneva_overview_top_with_district_subplots(
        DISTRICT_CSV_FILES=[
            "data/Rural.csv",
            "data/Villa.csv",
            "data/Center.csv",

        ],
        DISTRICT_PERIM_FILES=[
            "data/rural.txt",
            "data/villa.txt",
            "data/center.txt"
        ],
        DISTRICT_LABELS=[ "Rural",  "Villa", "Center"],
        filename="geneva_overview_top_with_subplots",
        basemap=True,
        overview_zoom_out=0.35
        #basemap_provider=ctx.providers.CartoDB.PositronNoLabels,
    )