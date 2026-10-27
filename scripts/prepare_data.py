"""UNTESTED starter. Run locally with internet: pip install pandas geopandas openpyxl
1. Download WUAFDCNRM202021.xlsx and WUAFDCASGS202021.xlsx from the ABS release page into data/raw/
2. Download the ABARES catchment land use 2023 and Australian Irrigation Areas shapefiles into data/raw/
3. Inspect sheet names / columns (pd.read_excel(..., sheet_name=None)), then adapt below.
Output: simplified GeoJSON (<1 MB) + joined values, used by the map specs you add to specs/."""
import pandas as pd, geopandas as gpd
sheets = pd.read_excel("data/raw/WUAFDCNRM202021.xlsx", sheet_name=None, header=None)
print({k: v.shape for k, v in sheets.items()})  # find the irrigated-area table, then clean it
# nrm = gpd.read_file("data/raw/NRM_2016.shp").to_crs(4326)
# nrm["geometry"] = nrm.simplify(0.02)
# nrm.merge(irrigated_ha_df, on="NRM_NAME").to_file("data/nrm_irrigation.geojson", driver="GeoJSON")
