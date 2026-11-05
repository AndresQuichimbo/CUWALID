import os
import time
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray
import matplotlib.pyplot as plt
from datetime import datetime

# Import structural builders directly from your main code base
from DRYP_read_datasets import _build_linear_interp_weights, _apply_separable_linear_interp

def run_interpolation_and_plot(imerg_nc_path, dem_raster_path, field_name='precipitation', output_png='imerg_comparison_grid.png'):
    print("="*70)
    print("   DRYP HYDROLOGICAL MODEL - VISUAL RESAMPLING BENCHMARK")
    print("="*70)
    
    # -------------------------------------------------------------------------
    # 1. LOAD TARGET SPACE HIGH-RESOLUTION DEM
    # -------------------------------------------------------------------------
    print(f"[*] Opening high-resolution target grid DEM: {os.path.basename(dem_raster_path)}")
    dem = rioxarray.open_rasterio(dem_raster_path)
    
    # Ensure standard names and sort coordinates cleanly
    if 'y' in dem.coords: dem = dem.rename({'y': 'lat', 'x': 'lon'})
    dem = dem.sortby('lat').sortby('lon')
    
    # Strip away optional band dimensions if necessary
    if dem.ndim == 3:
        dem = dem.isel(band=0)
        
    target_lat = np.asarray(dem['lat'].values, dtype=np.float64)
    target_lon = np.asarray(dem['lon'].values, dtype=np.float64)
    fine_dem = np.asarray(dem.values, dtype=np.float32)
    
    # -------------------------------------------------------------------------
    # 2. LOAD COARSE IMERG NETCDF FILE
    # -------------------------------------------------------------------------
    print(f"[*] Opening source IMERG monthly file: {os.path.basename(imerg_nc_path)}")
    ds_imerg = xr.open_dataset(imerg_nc_path)
    
    if 'latitude' in ds_imerg.coords: ds_imerg = ds_imerg.rename({'longitude':'lon', 'latitude':'lat'})
    if 'X' in ds_imerg.coords: ds_imerg = ds_imerg.rename({'X':'lon', 'Y':'lat'})
    ds_imerg = ds_imerg.sortby('lat').sortby('lon')
    
    if field_name not in ds_imerg.variables:
        possible_vars = [v for v in ['pre', 'rain', 'precipitation'] if v in ds_imerg.variables]
        if possible_vars: field_name = possible_vars[0]
        else: raise KeyError(f"Could not find field variable in IMERG. Found: {list(ds_imerg.variables)}")

    # -------------------------------------------------------------------------
    # 3. PRECOMPUTE WEIGHTS & COARSE BASES (ONCE)
    # -------------------------------------------------------------------------
    print("[*] Generating precomputed weight arrays and coarse DEM baselines...")
    src_sample = ds_imerg[field_name].isel(time=0).transpose('lat', 'lon')
    src_lat = np.asarray(src_sample['lat'].values, dtype=np.float64)
    src_lon = np.asarray(src_sample['lon'].values, dtype=np.float64)
    
    lat_w_pair = _build_linear_interp_weights(src_lat, target_lat)
    lon_w_pair = _build_linear_interp_weights(src_lon, target_lon)
    
    # Generate the coarse baseline model layout
    coarse_tmp = dem.coarsen(lat=12, lon=12, boundary='pad', side='pad').mean()
    coarse_dem_mapped = coarse_tmp.interp(lat=dem.lat, lon=dem.lon, method='linear')
    coarse_dem_upscaled = np.asarray(coarse_dem_mapped.values, dtype=np.float32)

    # -------------------------------------------------------------------------
    # 4. PREPARE PLOTTING CANVAS & ZOOM SUBSPACE MASK
    # -------------------------------------------------------------------------
    # To view true pixel variation, we zoom into a localized window 
    # Pick a 1-degree coordinate window containing active rainfall data
    zoom_lat_min, zoom_lat_max = target_lat.min() + (target_lat.max() - target_lat.min())/2, target_lat.min() + (target_lat.max() - target_lat.min())/2 + 1.0
    zoom_lon_min, zoom_lon_max = target_lon.min() + (target_lon.max() - target_lon.min())/2, target_lon.min() + (target_lon.max() - target_lon.min())/2 + 1.0
    
    lat_mask_tgt = (target_lat >= zoom_lat_min) & (target_lat <= zoom_lat_max)
    lon_mask_tgt = (target_lon >= zoom_lon_min) & (target_lon <= zoom_lon_max)
    lat_mask_src = (src_lat >= zoom_lat_min - 0.2) & (src_lat <= zoom_lat_max + 0.2)
    lon_mask_src = (src_lon >= zoom_lon_min - 0.2) & (src_lon <= zoom_lon_max + 0.2)

    fig, axes = plt.subplots(3, 4, figsize=(18, 12), sharex='col', sharey='row')
    cmap_rain = 'Blues' # Standard hydrologic palette

    # -------------------------------------------------------------------------
    # 5. TIMESTEP LOOP AND RUNTIME PLOTTING
    # -------------------------------------------------------------------------
    for step in range(3):
        print(f"\n[TIMESTEP INDEX: {step}] processing arrays...")
        da_step = ds_imerg[field_name].isel(time=step).transpose('lat', 'lon')
        raw_data_2d = np.asarray(da_step.values, dtype=np.float32)
        
        # Method A: Standard Dynamic Xarray Linear
        t0 = time.perf_counter()
        ds_linear = da_step.interp(lat=target_lat, lon=target_lon, method="linear")
        arr_linear = np.asarray(ds_linear.values, dtype=np.float32)
        t_linear = time.perf_counter() - t0
        
        # Method B: Precomputed Bilinear Lookups
        t0 = time.perf_counter()
        arr_precalc = _apply_separable_linear_interp(raw_data_2d, lat_w_pair, lon_w_pair)
        t_precalc = time.perf_counter() - t0
        
        # Method C: Mass Conservative Topographic Delta
        t0 = time.perf_counter()
        base_grid = _apply_separable_linear_interp(raw_data_2d, lat_w_pair, lon_w_pair)
        elevation_diff = fine_dem - coarse_dem_upscaled
        lapse_modifier = np.clip(1.0 + (elevation_diff / 100.0) * 0.06, 0.1, 2.5)
        arr_delta = base_grid * lapse_modifier
        t_delta = time.perf_counter() - t0
        
        print(f"  -> Method A (Standard Linear): Time = {t_linear*1000:.2f} ms")
        print(f"  -> Method B (Precalc Weights): Time = {t_precalc*1000:.2f} ms")
        print(f"  -> Method C (Mass Delta):      Time = {t_delta*1000:.2f} ms")
        
        # --- Slice sub-arrays exclusively for clear visualization display ---
        plot_src = raw_data_2d[lat_mask_src, :][:, lon_mask_src]
        plot_linear = arr_linear[lat_mask_tgt, :][:, lon_mask_tgt]
        plot_precalc = arr_precalc[lat_mask_tgt, :][:, lon_mask_tgt]
        plot_delta = arr_delta[lat_mask_tgt, :][:, lon_mask_tgt]
        
        # Dynamically evaluate the local vmin/vmax range bounds to maximize color contrast
        vmax = max(1e-3, np.nanmax(plot_delta))
        
        # Row layout configuration plotting
        ax_row = axes[step]
        
        # Col 1: Original Coarse IMERG Input Data
        im0 = ax_row[0].imshow(plot_src, origin='lower', cmap=cmap_rain, vmax=vmax, extent=[zoom_lon_min-0.2, zoom_lon_max+0.2, zoom_lat_min-0.2, zoom_lat_max+0.2])
        ax_row[0].set_ylabel(f"Timestep {step}\nLatitude")
        
        # Col 2: Standard Xarray Linear
        im1 = ax_row[1].imshow(plot_linear, origin='lower', cmap=cmap_rain, vmax=vmax, extent=[zoom_lon_min, zoom_lon_max, zoom_lat_min, zoom_lat_max])
        
        # Col 3: Precomputed Weights Interpolation Lookups
        im2 = ax_row[2].imshow(plot_precalc, origin='lower', cmap=cmap_rain, vmax=vmax, extent=[zoom_lon_min, zoom_lon_max, zoom_lat_min, zoom_lat_max])
        
        # Col 4: Topographic Mass Conservative Delta
        im3 = ax_row[3].imshow(plot_delta, origin='lower', cmap=cmap_rain, vmax=vmax, extent=[zoom_lon_min, zoom_lon_max, zoom_lat_min, zoom_lat_max])
        
        # Synchronize colorbars per row context to handle storm variations
        fig.colorbar(im3, ax=ax_row.tolist(), orientation='vertical', shrink=0.7, label='Precipitation Intensity (mm/hr)')

    # Add Column Header Identifiers
    axes[0, 0].set_title("1. Original Coarse Input\n(IMERG Native 0.1° Grid)", fontsize=11, fontweight='bold')
    axes[0, 1].set_title("2. Standard Approach\n(Dynamic xarray Linear)", fontsize=11, fontweight='bold')
    axes[0, 2].set_title("3. Fast Approach\n(Precomputed Bilinear LUT)", fontsize=11, fontweight='bold')
    axes[0, 3].set_title("4. Orographic Approach\n(Mass Conservative Delta)", fontsize=11, fontweight='bold')
    
    for ax in axes[-1, :]:
        ax.set_xlabel("Longitude")

    plt.suptitle("DRYP Hydrological Model - Spatial Resolution Downscaling Interpolation Comparisons", fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    # Save directly into current working directory
    plt.savefig(output_png, dpi=200, bbox_inches='tight')
    print(f"\n[+] Visual matrix grid file exported successfully to disk: '{output_png}'")
    plt.close()


# -------------------------------------------------------------------------
# EXECUTION ENTRY POINT - UPDATE SYSTEM FILE PATHS HERE
# -------------------------------------------------------------------------
if __name__ == "__main__":
    # Replace these paths with actual file directories on your HPC workspace environment
    IMERG_TEST_FILE = "/home/chc-andres/AF/datasets/climatology/IMERG/monthly/YYYY/IMERG_Africa_1h_200210.nc"
    DEM_TEST_RASTER = "/home/chc-andres/AF/historical/continental/datasets/hyd_af_dem_30s.tif" 
    
    if not os.path.exists(IMERG_TEST_FILE) or not os.path.exists(DEM_TEST_RASTER):
        print("[!] Execution Halted: Please configure valid paths inside the script pointing to your dataset test objects.")
    else:
        run_interpolation_and_plot(IMERG_TEST_FILE, DEM_TEST_RASTER)