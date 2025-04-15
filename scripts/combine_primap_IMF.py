"""script to combine the climate trace and primap data

Before running this script, copy the primap release of your
choice to the `vis_tool_data` folder
"""

# from climate_trace_data_primap.paths import extracted_data_path, vis_tool_data_path

import primap2 as pm

# read primap data set
primap_25 = pm.open_dataset(
    "../data/Guetschow_et_al_2025-PRIMAP-hist_v2.6.1_final_13-Mar-2025.nc"
)

# read climate trace data set
imf = pm.open_dataset("../data/IMF_out.nc")
imf = imf.drop_vars(["scenario (IMF)"])
# rename so it will be merged with primap source dimension
imf = imf.rename({"source": "scenario (PRIMAP-hist)"})

# read primap data
ds = primap_25.pr.merge(imf)
# TODO There's probably a better way to do this
ds = ds.rename({"scenario (PRIMAP-hist)": "SourceScen"})
ds = ds.drop_vars(["source"])
ds = ds.squeeze(["source", "scenario (IMF)"])
ds.attrs = primap_25.attrs
# TODO delete next line when primap2 is updated
ds = ds.drop_encoding()
ds.pr.to_netcdf("../data/imf_primap_comparison.nc")
