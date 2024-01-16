"""# noqa: D300

Make a small data set with only 5 years for quicker testing.

"""
from pathlib import Path

import primap2 as pm

root_folder = Path(__file__).parent.parent
data_folder = Path("data")
ds = pm.open_dataset(
    root_folder / data_folder / "combined_data_v2.5_final_v2.4.2_final.nc"
)

ds_small = ds.isel(time=range(-5, 0, 1))
ds_small.pr.to_netcdf(root_folder / data_folder / "test_ds.nc")
