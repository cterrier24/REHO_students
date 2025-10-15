#!/usr/bin/env python3
"""
Plot Swiss map with district-level REHO metrics.
Users can choose between TOTEX or GWP reduction metrics, and whether to use cached data.

Usage:
    python run_map_plot.py              # Use cached metrics if available
    python run_map_plot.py --recalc     # Force recalculation of metrics

Configuration:
    - Set METRIC_TYPE to 'TOTEX' or 'GWP' to choose which metric to plot
    - Set USE_ENRICHED to True to calculate reduction metrics, False for basic dots
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union
import rasterio
import rasterio.mask
from rasterio.warp import reproject
from rasterio.enums import Resampling
from rasterio.transform import Affine
from rasterio.plot import show as rioshow

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from matplotlib.colors import Normalize, ListedColormap, LinearSegmentedColormap
import matplotlib.cm as cm
from datetime import datetime
from matplotlib_scalebar.scalebar import ScaleBar

# =============================================================================
# USER CONFIGURATION
# =============================================================================
# Set the metric type to plot: 'TOTEX' or 'GWP'
METRIC_TYPE = 'TOTEX'  # Change to 'GWP' to plot GWP reduction

# Use enriched dots with REHO metrics (reduction) or basic dots
USE_ENRICHED = True  # Set to False to use dots_merged

# Paths
REHO_RESULTS_PATH = "../../results/CH"
MAP_DIR = ""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_energy_colormap(cmap_type: str = "efficiency"):
	"""
	Get energy-specific colormaps for different metrics.

	Parameters
	----------
	cmap_type : str
		Type of energy colormap. Options: 'efficiency', 'capacity', 'cost', 'renewable', 'discrete', 'continuous_builtin'

	Returns
	-------
	matplotlib.colors.Colormap
		Energy-specific colormap (continuous or discrete)
	"""
	if cmap_type == "efficiency":
		# Green to red for efficiency (high=good, low=bad)
		colors = ['#d73027', '#f46d43', '#fdae61', '#fee08b', '#e6f598', '#abdda4', '#66c2a5', '#3288bd']
		return LinearSegmentedColormap.from_list('energy_efficiency', colors[::-1], N=256)
	elif cmap_type == "capacity":
		# Blue gradient for capacity
		colors = ['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#084594']
		return LinearSegmentedColormap.from_list('energy_capacity', colors, N=256)
	elif cmap_type == "cost":
		# Yellow to red for cost (low=good, high=bad)
		colors = ['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#b10026']
		return LinearSegmentedColormap.from_list('energy_cost', colors, N=256)
	elif cmap_type == "renewable":
		# Green gradient for renewable energy
		colors = ['#f7fcf5', '#e5f5e0', '#c7e9c0', '#a1d99b', '#74c476', '#41ab5d', '#238b45', '#005a32']
		return LinearSegmentedColormap.from_list('energy_renewable', colors, N=256)
	elif cmap_type == "continuous_builtin":
		# Fallback to guaranteed continuous built-in colormap
		return cm.get_cmap("RdYlGn_r")  # Red-Yellow-Green reversed (good=green)
	elif cmap_type == "discrete":
		# Discrete colors for categorical data
		colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf']
		return ListedColormap(colors, name='energy_discrete')
	else:
		# Default continuous colormap
		return cm.get_cmap(cmap_type)


def _rgb_to_gray(data):
	"""
	Convert a multiband raster array to a single-band grayscale image.

	Parameters
	----------
	data : np.ndarray
		Array shaped (bands, H, W). If it has ≥3 bands, use sRGB luminance
		weights (0.2126*R + 0.7152*G + 0.0722*B). Otherwise use band 1.

	Returns
	-------
	np.ndarray
		2D array (H, W) of float32 grayscale values.
	"""
	if data.shape[0] >= 3:
		R, G, B = data[0].astype("float32"), data[1].astype("float32"), data[2].astype("float32")
		gray = 0.2126 * R + 0.7152 * G + 0.0722 * B
		return gray
	else:
		return data[0].astype("float32")


def _resample_after_mask(data, transform, crs, scale, resampling=Resampling.nearest):
	"""
	Resample a cropped raster by an integer `scale` using rasterio.reproject.
	"""
	if scale == 1:
		return data, transform
	count, h, w = data.shape
	H, W = max(1, h // scale), max(1, w // scale)
	dst = np.empty((count, H, W), dtype=data.dtype)
	new_transform = transform * Affine.scale(scale)
	reproject(
		source=data,
		destination=dst,
		src_transform=transform, src_crs=crs,
		dst_transform=new_transform, dst_crs=crs,
		resampling=resampling,
	)
	return dst, new_transform


def plot_map(
	raster_path: str,
	dots_proj: gpd.GeoDataFrame,
	out_path: str,
	dot_size_pts: float,
	dot_alpha: float,
	dot_edgewidth: float,
	fig_w: float,
	fig_h: float,
	fig_dpi: int,
	bg_alpha: float,
	mask_path: str,
	quality: str,
	color_column: str | None = None,
	legend: bool = True,
	vmin: float | None = None,
	vmax: float | None = None,
	auto_scale: str | None = None,
	basemap_mode: str = "color",
	dot_marker: str = 'o',
	cbar_labelsize: int = 18,
	cbar_ticksize: int = 18,
	cbar_pad: float = 0.02,
	cbar_shrink: float = 0.5,
	cbar_aspect: int = 35,
	title: str | None = None,
	subtitle: str | None = None,
	data_source: str | None = None,
	show_scale_bar: bool = True,
	show_north_arrow: bool = True,
	adaptive_sizing: bool = False,
	size_column: str | None = None,
	boundary_style: dict | None = None,
	annotations: list | None = None,
	cmap_type: str | None = None,
	legend_percentage: bool = False,
	net_balance_point: dict | None = None,
	legend_label = ""
):
	"""
	Render the basemap and overlay dot clusters colored by an indicator.
	"""
	# Set up energy-specific colormap if requested
	if cmap_type:
		try:
			cmap = get_energy_colormap(cmap_type)
		except:
			cmap = cm.get_cmap("RdYlGn_r")
	else:
		cmap = cm.get_cmap("RdYlGn_r")

	# Set default boundary style
	if boundary_style is None:
		boundary_style = {
			'edgecolor': 'black',
			'linewidth': 1.0,
			'facecolor': 'none',
			'linestyle': '-'
		}

	# Create figure
	fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=fig_dpi)

	with rasterio.open(raster_path) as ds:
		boundary = gpd.read_file(mask_path).to_crs(ds.crs) if mask_path else None
		if boundary is not None:
			mask_geom = [unary_union(boundary.geometry)]

			data, transform = rasterio.mask.mask(ds, mask_geom, crop=True, filled=True, nodata=0)

			ovr = ds.overviews(1) or []
			if quality == "full" or not ovr:
				scale = 1
			elif quality == "high":
				scale = int(ovr[0])
			elif quality == "med":
				scale = int(ovr[len(ovr)//2])
			else:
				scale = int(ovr[-1])

			show_data, show_transform = _resample_after_mask(
				data, transform, ds.crs, scale, resampling=Resampling.nearest
			)

			# Make OUTSIDE white
			if show_data.shape[0] == 1:
				outside = (show_data[0] == 0)
			else:
				outside = np.all(show_data == 0, axis=0)

			if basemap_mode.lower() == "gray":
				gray = _rgb_to_gray(show_data)
				gray_out = gray.copy()
				if np.issubdtype(show_data.dtype, np.integer):
					white = np.iinfo(show_data.dtype).max
				else:
					white = np.nanmax(gray) if np.isfinite(gray).any() else 1.0
				gray_out[outside] = white

				try:
					lo, hi = np.percentile(gray[~outside], (2, 98))
				except Exception:
					lo, hi = None, None

				rioshow(gray_out, transform=show_transform, ax=ax, cmap="gray", vmin=lo, vmax=hi, alpha=bg_alpha)
			else:
				rgb = show_data.copy()
				if np.issubdtype(rgb.dtype, np.integer):
					white = np.iinfo(rgb.dtype).max
				else:
					white = 1.0
				for b in range(min(3, rgb.shape[0])):
					band = rgb[b]
					band[outside] = white
					rgb[b] = band
				rioshow(rgb, transform=show_transform, ax=ax, alpha=bg_alpha)

			dots_in = dots_proj.to_crs(ds.crs)
			minx, miny, maxx, maxy = boundary.total_bounds
			dots_in = dots_in.cx[minx:maxx, miny:maxy]

			# Enhanced boundary styling
			boundary.boundary.plot(ax=ax, edgecolor="white", linewidth=boundary_style['linewidth'] + 1.5,
								 facecolor="none", zorder=15)
			boundary.boundary.plot(ax=ax,
								 edgecolor=boundary_style['edgecolor'],
								 linewidth=boundary_style['linewidth'],
								 facecolor=boundary_style['facecolor'],
								 linestyle=boundary_style.get('linestyle', '-'),
								 zorder=16)

		else:
			# No mask: read at high detail
			ovr = ds.overviews(1) or []
			if ovr:
				scale = int(ovr[0])
				out_shape = (ds.count, max(1, ds.height // scale), max(1, ds.width // scale))
				data = ds.read(out_shape=out_shape, resampling=Resampling.nearest)
				transform = ds.transform * Affine.scale(scale)
			else:
				data = ds.read()
				transform = ds.transform

			if basemap_mode.lower() == "gray":
				gray = _rgb_to_gray(data)
				try:
					lo, hi = np.percentile(gray[np.isfinite(gray)], (2, 98))
				except Exception:
					lo, hi = None, None
				rioshow(gray, transform=transform, ax=ax, cmap="gray",
						vmin=lo, vmax=hi, alpha=bg_alpha)
			else:
				rioshow(data, transform=transform, ax=ax, alpha=bg_alpha)

	# Choose which dots to draw
	to_plot = dots_in if (mask_path and 'dots_in' in locals()) else dots_proj

	# Calculate adaptive sizing if requested
	if adaptive_sizing and size_column and size_column in to_plot.columns:
		size_values = to_plot[size_column]
		min_size, max_size = dot_size_pts * 0.5, dot_size_pts * 2
		normalized_sizes = (size_values - size_values.min()) / (size_values.max() - size_values.min())
		dot_sizes = min_size + normalized_sizes * (max_size - min_size)
	else:
		dot_sizes = dot_size_pts

	# Plot dots: colored by indicator if provided
	if color_column and (color_column in to_plot.columns):
		if adaptive_sizing and size_column and size_column in to_plot.columns:
			scatter = ax.scatter(
				to_plot.geometry.x, to_plot.geometry.y,
				c=to_plot[color_column],
				s=dot_sizes,
				marker=dot_marker,
				alpha=dot_alpha,
				cmap=cmap,
				vmin=vmin,
				vmax=vmax,
				edgecolors='none' if dot_edgewidth == 0 else 'black',
				linewidths=dot_edgewidth,
				zorder=10
			)
		else:
			to_plot.plot(
				ax=ax,
				column=color_column,
				cmap=cmap,
				markersize=dot_size_pts,
				marker=dot_marker,
				edgecolor=None,
				linewidth=dot_edgewidth,
				alpha=dot_alpha,
				vmin=vmin,
				vmax=vmax,
				legend=False,
			)

		# Enhanced colorbar
		if legend:
			if vmin is None or vmax is None:
				if auto_scale == "percentile":
					p5, p95 = np.percentile(to_plot[color_column].dropna(), [5, 95])
					_vmin = p5 if vmin is None else vmin
					_vmax = p95 if vmax is None else vmax
				elif auto_scale == "robust":
					p1, p99 = np.percentile(to_plot[color_column].dropna(), [1, 99])
					_vmin = p1 if vmin is None else vmin
					_vmax = p99 if vmax is None else vmax
				elif auto_scale == "symmetric":
					abs_max = max(abs(to_plot[color_column].min()), abs(to_plot[color_column].max()))
					_vmin = -abs_max if vmin is None else vmin
					_vmax = abs_max if vmax is None else vmax
				else:
					_vmin = float(to_plot[color_column].min()) if vmin is None else vmin
					_vmax = float(to_plot[color_column].max()) if vmax is None else vmax
			else:
				_vmin = vmin
				_vmax = vmax

			_fmt = PercentFormatter(xmax=1, decimals=0) if legend_percentage else None

			sm = cm.ScalarMappable(norm=Normalize(vmin=_vmin, vmax=_vmax), cmap=cmap)
			sm.set_array([])

			cbar = fig.colorbar(
				sm, ax=ax, orientation="horizontal", pad=cbar_pad,
				shrink=cbar_shrink, aspect=cbar_aspect, format=_fmt,
				extend='neither',
				drawedges=False,
				spacing='proportional',
				boundaries=None,
				ticks=None
			)

			cbar.set_label(legend_label, fontsize=cbar_labelsize, labelpad=10)
			cbar.ax.tick_params(labelsize=cbar_ticksize, direction='out',
							  length=4, width=1, colors='black')

			try:
				cbar.outline.set_linewidth(0.8)
				cbar.outline.set_edgecolor('black')
				cbar.ax.patch.set_facecolor('white')
				cbar.ax.patch.set_alpha(0.9)
			except Exception:
				pass
	else:
		to_plot.plot(
			ax=ax,
			markersize=dot_size_pts,
			marker=dot_marker,
			facecolor="white",
			edgecolor="black",
			linewidth=dot_edgewidth,
			alpha=dot_alpha,
		)

	ax.set_axis_off()

	# Add title and subtitle if provided
	if title:
		fig.suptitle(title, fontsize=16, fontweight='bold', y=0.95)
	if subtitle:
		title_y = 0.92 if title else 0.95
		fig.text(0.5, title_y, subtitle, ha='center', fontsize=12, style='italic')

	# Add data source annotation
	if data_source:
		source_text = f"Source: {data_source}"
		timestamp = datetime.now().strftime("%Y-%m-%d")
		full_source = f"{source_text} | Generated: {timestamp}"
		fig.text(0.02, 0.02, full_source, fontsize=8, alpha=0.7,
				transform=fig.transFigure)

	# Add scale bar if requested
	if show_scale_bar and boundary is not None:
		try:
			scalebar = ScaleBar(1, units="m", location="lower right",
							  box_alpha=0.8, color='black')
			ax.add_artist(scalebar)
		except Exception:
			pass

	# Add north arrow if requested
	if show_north_arrow:
		try:
			arrow_x, arrow_y = 0.95, 0.9
			ax.annotate('N', xy=(arrow_x, arrow_y), xycoords='axes fraction',
					   fontsize=14, fontweight='bold', ha='center', va='center')
			ax.annotate('↑', xy=(arrow_x, arrow_y - 0.03), xycoords='axes fraction',
					   fontsize=16, ha='center', va='center')
		except Exception:
			pass

	# Add custom annotations if provided
	if annotations:
		for annotation in annotations:
			try:
				ax.annotate(
					annotation.get('text', ''),
					xy=annotation.get('xy', (0, 0)),
					xycoords=annotation.get('xycoords', 'data'),
					fontsize=annotation.get('fontsize', 10),
					ha=annotation.get('ha', 'center'),
					va=annotation.get('va', 'center'),
					bbox=annotation.get('bbox', dict(boxstyle="round,pad=0.3",
													facecolor='white', alpha=0.8))
				)
			except Exception:
				pass

	fig.tight_layout()
	fig.show()
	fig.savefig(out_path, bbox_inches="tight", dpi=fig_dpi, transparent=False)
	print(f"Saved map to: {out_path}")


def load_dots_data(plot_key: str):
	"""Load dots data from gpkg file."""
	print(f"Loading dots data...")
	dots = gpd.read_file("dots_merged.gpkg")
	print(f"Successfully loaded dots_merged.gpkg with {len(dots)} dots")
	return dots


def calculate_totex_per_capita(pickle_path):
	"""
	Calculate TOTEX per capita from a REHO results pickle file.

	Parameters
	----------
	pickle_path : str
		Path to the pickle file (9a or 9c)

	Returns
	-------
	float
		TOTEX per capita in CHF/person/year
	"""
	import pickle

	with open(pickle_path, 'rb') as f:
		data = pickle.load(f)

	result = data['actors'][0]
	perf = result['df_Performance']
	costs_op = float(perf.loc['Network', 'Costs_op'])
	costs_inv = float(perf.loc['Network', 'Costs_inv'])
	buildings = result['df_Buildings']
	total_era = float(buildings['ERA'].sum())
	totex_per_capita = (costs_op + costs_inv) / total_era * 46

	return totex_per_capita


def calculate_gwp_per_capita(pickle_path):
	"""
	Calculate GWP per capita from a REHO results pickle file.

	Parameters
	----------
	pickle_path : str
		Path to the pickle file

	Returns
	-------
	float
		GWP per capita in tCO2-eq/person/year (including vehicle emissions)
	"""
	import pickle

	with open(pickle_path, 'rb') as f:
		data = pickle.load(f)

	result = data['actors'][0]
	perf = result['df_Performance']
	gwp_constr = float(perf.loc['Network', 'GWP_constr'])
	gwp_op = float(perf.loc['Network', 'GWP_op'])
	buildings = result['df_Buildings']
	total_era = float(buildings['ERA'].sum())
	gwp_per_capita = (gwp_constr + gwp_op) / total_era * 46 / 1000

	return gwp_per_capita


def enrich_dots_with_reho_metrics(dots: gpd.GeoDataFrame, reho_results_path: str):
	"""
	Enrich dots with TOTEX-Reduction and GWP-Reduction metrics from REHO results.

	Parameters
	----------
	dots : GeoDataFrame
		Dots with cluster_id column
	reho_results_path : str
		Path to directory containing 9a_ and 9c_ pickle files

	Returns
	-------
	GeoDataFrame
		Dots enriched with TOTEX_Reduction and GWP_Reduction columns
	"""
	# District name mapping based on cluster_id
	name_to_district = {
		0: 'Geltwil', 1: 'Bisikon', 2: 'Liddes', 3: 'Wettingen',
		4: 'Vionnaz', 5: 'Basel', 6: 'Litau', 7: 'Finsterwald',
		8: 'Sunneberg', 9: 'Sissach', 10: 'Schuepfen', 11: 'Zuerich',
	}

	# Vehicle GWP constants
	ICE_vehicle_gwp = 5.6 / 10 / 1.6  # tCO2-eq per person per year
	E_vehicle_gwp = 1.5 * ICE_vehicle_gwp

	# Calculate metrics for each district
	metrics = {}

	for cluster_id, district_name in name_to_district.items():
		# Build file paths
		file_9a = Path(reho_results_path) / f"9a_{district_name}_TOTEX_wo_El.pickle"
		file_9c = Path(reho_results_path) / f"9c_{district_name}_Actors.pickle"

		# Check if files exist
		if not file_9a.exists() or not file_9c.exists():
			print(f"Warning: Missing files for {district_name} (cluster {cluster_id})")
			continue

		try:
			# Calculate TOTEX per capita before and after
			totex_before = calculate_totex_per_capita(str(file_9a))
			totex_after = calculate_totex_per_capita(str(file_9c))
			totex_reduction = totex_before - totex_after

			# Calculate GWP per capita before and after (including vehicle emissions)
			gwp_before = calculate_gwp_per_capita(str(file_9a)) + ICE_vehicle_gwp
			gwp_after = calculate_gwp_per_capita(str(file_9c)) + E_vehicle_gwp
			gwp_reduction = gwp_before - gwp_after

			metrics[cluster_id] = {
				'TOTEX_Reduction': totex_reduction,
				'GWP_Reduction': gwp_reduction,
				'TOTEX_before': totex_before,
				'TOTEX_after': totex_after,
				'GWP_before': gwp_before,
				'GWP_after': gwp_after,
			}

			print(f"{district_name} (cluster {cluster_id}): TOTEX reduction = {totex_reduction:.2f} CHF/cap/yr, "
				  f"GWP reduction = {gwp_reduction:.3f} tCO2-eq/cap/yr")

		except Exception as e:
			print(f"Error processing {district_name}: {e}")
			continue

	# Add metrics to dots
	dots_enriched = dots.copy()
	dots_enriched['TOTEX_Reduction'] = dots_enriched['cluster_id'].map(
		lambda x: metrics.get(x, {}).get('TOTEX_Reduction', np.nan) if pd.notnull(x) else np.nan
	)
	dots_enriched['GWP_Reduction'] = dots_enriched['cluster_id'].map(
		lambda x: metrics.get(x, {}).get('GWP_Reduction', np.nan) if pd.notnull(x) else np.nan
	)
	dots_enriched['TOTEX_before'] = dots_enriched['cluster_id'].map(
		lambda x: metrics.get(x, {}).get('TOTEX_before', np.nan) if pd.notnull(x) else np.nan
	)
	dots_enriched['TOTEX_after'] = dots_enriched['cluster_id'].map(
		lambda x: metrics.get(x, {}).get('TOTEX_after', np.nan) if pd.notnull(x) else np.nan
	)
	dots_enriched['GWP_before'] = dots_enriched['cluster_id'].map(
		lambda x: metrics.get(x, {}).get('GWP_before', np.nan) if pd.notnull(x) else np.nan
	)
	dots_enriched['GWP_after'] = dots_enriched['cluster_id'].map(
		lambda x: metrics.get(x, {}).get('GWP_after', np.nan) if pd.notnull(x) else np.nan
	)

	return dots_enriched


# =============================================================================
# MAIN SCRIPT
# =============================================================================

if __name__ == "__main__":

	# Check for command-line arguments
	force_recalc = '--recalc' in sys.argv or '-r' in sys.argv

	# Set plot key based on metric type
	if METRIC_TYPE.upper() == 'TOTEX':
		plot_key = 'TOTEX_Reduction'
		legend_label = 'TOTEX Reduction [CHF/capita/year]'
		cmap_type = 'cost'
	elif METRIC_TYPE.upper() == 'GWP':
		plot_key = 'GWP_Reduction'
		legend_label = 'GWP Reduction [tCO₂-eq/capita/year]'
		cmap_type = 'renewable'
	else:
		raise ValueError("METRIC_TYPE must be 'TOTEX' or 'GWP'")

	# Configure based on USE_ENRICHED flag
	if USE_ENRICHED:
		enriched_dots_path = "dots_enriched_with_metrics.gpkg"

		# Check if enriched dots already exist
		if os.path.exists(enriched_dots_path) and not force_recalc:
			print(f"Loading pre-calculated metrics from {enriched_dots_path}...")
			dots = gpd.read_file(enriched_dots_path)
			print(f"Loaded {len(dots)} dots with cached metrics")
		else:
			dots = None

		# If no cached data, calculate from scratch
		if dots is None:
			if force_recalc:
				print("Force recalculation requested...")

			# Load dots data
			print("Loading dots data...")
			dots = load_dots_data('cluster_id')
			print(f"Loaded {len(dots)} dots")

			# Enrich dots with REHO metrics
			print("\nCalculating TOTEX and GWP reductions for each district...")
			dots = enrich_dots_with_reho_metrics(dots, REHO_RESULTS_PATH)

			# Save enriched dots for future use
			print(f"\nSaving enriched dots to {enriched_dots_path}...")
			dots.to_file(enriched_dots_path, driver="GPKG")
			print("Cached metrics saved successfully!")

		# Check if we have any valid metrics
		valid_dots = dots[~dots[plot_key].isna()]
		print(f"\nDots with valid {plot_key}: {len(valid_dots)}")

		if len(valid_dots) == 0:
			print(f"ERROR: No valid {plot_key} data found!")
			print("Please check that the pickle files can be loaded correctly.")
			sys.exit(1)

	else:
		# Use basic dots without enrichment
		print("Loading basic dots data (no enrichment)...")
		dots = load_dots_data('cluster_id')
		print(f"Loaded {len(dots)} dots")
		plot_key = None  # No metric column to plot
		legend_label = None

	# Set up output path
	out_path = f"../plots/REHO_map_{METRIC_TYPE}.pdf"

	# Configure legend scaling
	vmin, vmax = None, None
	auto_scale = 'robust' if USE_ENRICHED else None

	print(f"\nPlotting {METRIC_TYPE}...")
	print(f"Output: {out_path}")

	try:
		plot_map(
			raster_path="CH_map.tif",
			dots_proj=dots,
			out_path=out_path,
			dot_size_pts=4,
			dot_alpha=0.8,
			dot_edgewidth=0,
			fig_w=12, fig_h=8, fig_dpi=300,
			bg_alpha=1,
			mask_path='boundaries_ch.gpkg',
			quality='high',
			color_column=plot_key,
			vmin=vmin,
			vmax=vmax,
			legend=USE_ENRICHED,
			basemap_mode="gray",
			dot_marker='s',
			title=None,
			subtitle=None,
			data_source=None,
			auto_scale=auto_scale,
			show_scale_bar=False,
			show_north_arrow=False,
			cmap_type=cmap_type if USE_ENRICHED else None,
			adaptive_sizing=True,
			size_column='metric_value' if 'metric_value' in dots.columns else None,
			boundary_style={'edgecolor': 'black', 'linewidth': 2.0, 'facecolor': 'none', 'linestyle': '-'},
			legend_percentage=False,
			legend_label=legend_label if USE_ENRICHED else '',
			cbar_labelsize=20,
			cbar_ticksize=16,
			cbar_pad=0.05,
			cbar_shrink=0.6,
			cbar_aspect=25
		)
		print(f"\nSuccess! Map saved to: {os.path.abspath(out_path)}")
	except Exception as e:
		print(f"\nError during plotting: {e}")
		import traceback
		traceback.print_exc()
		sys.exit(1)
