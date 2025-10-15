# Swiss Map Plotting for REHO Results

Simple script to generate maps of Switzerland showing district-level TOTEX or GWP reduction metrics from REHO optimization results.

## Quick Start

1. **Configure the script** - Edit `run_map_plot.py` lines 44-51:
   ```python
   METRIC_TYPE = 'TOTEX'  # or 'GWP'
   USE_ENRICHED = True    # True for reduction metrics, False for basic dots
   ```

2. **Run the script**:
   ```bash
   python run_map_plot.py
   ```

   Or force recalculation:
   ```bash
   python run_map_plot.py --recalc
   ```

## Configuration

### METRIC_TYPE
- `'TOTEX'`: Plot TOTEX reduction in CHF/capita/year
- `'GWP'`: Plot GWP reduction in tCO₂-eq/capita/year

### USE_ENRICHED
- `True`: Calculate and plot reduction metrics (before/after comparison)
  - Reads REHO results from `../../results/CH/`
  - Compares baseline (9a files) vs. electrification scenario (9c files)
  - Caches results in `dots_enriched_with_metrics.gpkg`
- `False`: Plot basic dots without metrics

## Input Files

The script expects the following files in the same directory:
- `dots_merged.gpkg` - Base dot locations
- `CH_map.tif` - Switzerland basemap raster
- `boundaries_ch.gpkg` - Swiss boundary shapefile

For enriched mode, REHO results in `../../results/CH/`:
- `9a_{district}_TOTEX_wo_El.pickle` - Baseline scenarios
- `9c_{district}_Actors.pickle` - Electrification scenarios

## Output

- Map saved as `../plots/REHO_map_{METRIC_TYPE}.pdf`
- Cached enriched data saved as `dots_enriched_with_metrics.gpkg`

## Districts

The script processes 12 districts:
- Geltwil, Bisikon, Liddes, Wettingen, Vionnaz, Basel
- Litau, Finsterwald, Sunneberg, Sissach, Schuepfen, Zuerich
