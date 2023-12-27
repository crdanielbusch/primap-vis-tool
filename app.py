"""
Launch plotly app.

Author: Daniel Busch, Date: 21-12-2023
"""

from pathlib import Path

import primap2 as pm  # type: ignore

#  define folders
print("Reading data set")
root_folder = Path(__file__).parent
data_folder = Path("data")
primaphist_data_folder = Path("data") / "PRIMAP-hist_data"

#  data reading
current_version = "v2.5_final"
old_version = "v2.4.2_final"
combined_ds = pm.open_dataset(
    root_folder / data_folder / f"combined_data_{current_version}_{old_version}.nc"
)
