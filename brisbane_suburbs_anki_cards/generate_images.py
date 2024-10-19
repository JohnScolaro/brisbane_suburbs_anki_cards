import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from typing import Literal
import os
from brisbane_suburbs_anki_cards import DOC_KML
from brisbane_suburbs_anki_cards.process_kml import get_localities_df
from brisbane_suburbs_anki_cards.constants import LOCAL_GOVERNMENT_AREAS_WE_CARE_ABOUT
import pandas as pd

ZOOM_OUT_FACTOR = 0.8  # 80%
TILE_SET: Literal["google", "openstreetmap"] = "openstreetmap"

# Special Case 1:
# Suburbs adjacent to similar named suburbs:
SPECIAL_CASE_1 = {
    "Chermside and Chermside West": {"Chermside", "Chermside West"},
    "Holland Park and Holland Park West": {"Holland Park", "Holland Park West"},
    "Kenmore and Kenmore Hills": {"Kenmore", "Kenmore Hills"},
    "Manly and Manly West": {"Manly", "Manly West"},
    "Mount Gravatt, Mount Gravatt East, and Upper Mount Gravatt": {
        "Mount Gravatt",
        "Upper Mount Gravatt",
        "Mount Gravatt East",
    },
    "Stafford and Stafford Heights": {"Stafford", "Stafford Heights"},
    "Sunnybank and Sunnybank Hills": {"Sunnybank", "Sunnybank Hills"},
    "Brookfield and Upper Brookfield": {"Brookfield", "Upper Brookfield"},
}
SPECIAL_CASE_1_LOCALITIES = set(
    locality for localities in SPECIAL_CASE_1.values() for locality in localities
)

# Special Case 2:
# You're a tiny locality on Moreton Island.
SPECIAL_CASE_2_LOCALITIES = {"Cowan Cowan", "Kooringal", "Bulwer"}

COLORS = ["#FFFFFF", "#4392F1"]


def get_output_path(output_type: str, locality_name: str) -> str:
    save_directory = os.path.join("output", output_type)
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    save_path = os.path.join(save_directory, f"{locality_name}.jpg")
    return save_path


def create_and_save_images() -> None:
    suburb_df = get_localities_df(DOC_KML)

    create_cards_for_localities(suburb_df)
    create_cards_for_special_case_1(suburb_df)
    create_cards_for_special_case_2(suburb_df)


def create_cards_for_localities(suburb_df: pd.DataFrame) -> None:
    """
    This function generates regular maps for all the localities in Brisbane.
    Even though some are later refined, it generates them for all of them
    because I still want the original worse maps, in case I want to use them
    for projects unrelated to this anki deck.
    """
    for geometry, locality, lga in suburb_df.itertuples(index=False):
        if lga not in LOCAL_GOVERNMENT_AREAS_WE_CARE_ABOUT:
            continue

        # Assign the selected suburb's geometry
        selected_suburb = gpd.GeoDataFrame(geometry=[geometry], crs=suburb_df.crs)

        # Reproject to Web Mercator (EPSG 3857) for compatibility with the basemap
        selected_suburb = selected_suburb.to_crs(epsg=3857)

        # Plot the selected suburb with a solid fill color
        ax = selected_suburb.plot(
            figsize=(5, 5), alpha=1.0, edgecolor="k", color="white"
        )

        # Get current bounds and expand them to zoom out
        minx, miny, maxx, maxy = selected_suburb.total_bounds

        # Calculate expanded bounds
        x_range = maxx - minx
        y_range = maxy - miny

        # Expand the bounds by the zoom-out factor
        minx -= x_range * ZOOM_OUT_FACTOR
        maxx += x_range * ZOOM_OUT_FACTOR
        miny -= y_range * ZOOM_OUT_FACTOR
        maxy += y_range * ZOOM_OUT_FACTOR

        # Determine the center and the maximum extent
        center_x = (minx + maxx) / 2
        center_y = (miny + maxy) / 2
        max_extent = max(maxx - minx, maxy - miny) / 2  # Half of the largest extent

        # Set new axis limits to ensure the plot is square
        ax.set_xlim(center_x - max_extent, center_x + max_extent)
        ax.set_ylim(center_y - max_extent, center_y + max_extent)

        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, attribution="")

        # Hide axes
        ax.set_axis_off()

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        # Save the plot to an image file
        plt.savefig(
            get_output_path("localities", locality),
            bbox_inches="tight",
            pad_inches=0,
            dpi=150,
            transparent=False,
        )
        plt.close()

        print(f"Map for {locality}, {lga} created!")


def create_cards_for_special_case_1(suburb_df: pd.DataFrame) -> None:
    """
    Creates a set of refined maps for "group suburbs" which are adjacent
    suburbs with very similar names. Designed to help remember where the
    suburbs are better, and also reduce card count.
    """
    dict_data = suburb_df.to_dict(orient="records")
    special_case_data = {
        k: [row["geometry"] for row in dict_data if row["locality"] in v]
        for k, v in SPECIAL_CASE_1.items()
    }

    for combined_locality_name, geometries in special_case_data.items():
        ax = None
        total_bounds = None
        for geometry in geometries:
            # Assign the selected suburb's geometry
            selected_suburb = gpd.GeoDataFrame(geometry=[geometry], crs=suburb_df.crs)

            # Reproject to Web Mercator (EPSG 3857) for compatibility with the basemap
            selected_suburb = selected_suburb.to_crs(epsg=3857)

            # Plot the selected suburb with a solid fill color, use the same ax for all geometries
            ax = selected_suburb.plot(
                ax=ax,  # Reuse the same axes object
                figsize=(5, 5),
                alpha=1.0,
                edgecolor="k",
                color="white",
            )

            if total_bounds is None:
                total_bounds = selected_suburb.total_bounds
            else:
                total_bounds = (
                    min(total_bounds[0], selected_suburb.total_bounds[0]),  # min x
                    min(total_bounds[1], selected_suburb.total_bounds[1]),  # min y
                    max(total_bounds[2], selected_suburb.total_bounds[2]),  # max x
                    max(total_bounds[3], selected_suburb.total_bounds[3]),  # max y
                )

        # Get current bounds and expand them to zoom out
        minx, miny, maxx, maxy = total_bounds

        # Calculate expanded bounds
        x_range = maxx - minx
        y_range = maxy - miny

        # Expand the bounds by the zoom-out factor
        minx -= x_range * ZOOM_OUT_FACTOR
        maxx += x_range * ZOOM_OUT_FACTOR
        miny -= y_range * ZOOM_OUT_FACTOR
        maxy += y_range * ZOOM_OUT_FACTOR

        # Determine the center and the maximum extent
        center_x = (minx + maxx) / 2
        center_y = (miny + maxy) / 2
        max_extent = max(maxx - minx, maxy - miny) / 2  # Half of the largest extent

        # Set new axis limits to ensure the plot is square
        ax.set_xlim(center_x - max_extent, center_x + max_extent)
        ax.set_ylim(center_y - max_extent, center_y + max_extent)

        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, attribution="")

        # Hide axes
        ax.set_axis_off()

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        # Save the plot to an image file
        plt.savefig(
            get_output_path("combined_localities", combined_locality_name),
            bbox_inches="tight",
            pad_inches=0,
            dpi=150,
            transparent=False,
        )
        plt.close()

        print(f"Special Case 1: Map for {combined_locality_name} created!")


def create_cards_for_special_case_2(suburb_df: pd.DataFrame) -> None:
    """
    Plots cards specifically for the micro-localities on Moreton Island. They
    are too small to see anything meaningful when you zoom in on the locality.
    """
    dict_data = suburb_df.to_dict(orient="records")
    moreton_island_geometry = next(
        iter(filter(lambda x: x["locality"] == "Moreton Island", dict_data))
    )["geometry"]
    micro_localities_geometry = {
        locality_name: next(
            iter(filter(lambda x: x["locality"] == locality_name, dict_data))
        )["geometry"]
        for locality_name in SPECIAL_CASE_2_LOCALITIES
    }

    # Variable to store the bounds of the center locality
    total_bounds = (
        gpd.GeoDataFrame(geometry=[moreton_island_geometry], crs=suburb_df.crs)
        .to_crs(epsg=3857)
        .total_bounds
    )

    for locality, geometry in micro_localities_geometry.items():
        # Assign the selected suburb's geometry
        selected_suburb = gpd.GeoDataFrame(geometry=[geometry], crs=suburb_df.crs)

        # Reproject to Web Mercator (EPSG 3857) for compatibility with the basemap
        selected_suburb = selected_suburb.to_crs(epsg=3857)

        # Plot the selected suburb with a solid fill color
        ax = selected_suburb.plot(
            figsize=(5, 5), alpha=1.0, edgecolor="k", color="white"
        )

        # Get current bounds and expand them to zoom out
        minx, miny, maxx, maxy = total_bounds

        # Determine the center and the maximum extent
        center_x = (minx + maxx) / 2
        center_y = (miny + maxy) / 2
        max_extent = max(maxx - minx, maxy - miny) / 2  # Half of the largest extent

        # Set new axis limits to ensure the plot is square
        ax.set_xlim(center_x - max_extent, center_x + max_extent)
        ax.set_ylim(center_y - max_extent, center_y + max_extent)

        ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, attribution="")

        # Hide axes
        ax.set_axis_off()

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        # Save the plot to an image file
        plt.savefig(
            get_output_path("moreton_island_localities", locality),
            bbox_inches="tight",
            pad_inches=0,
            dpi=150,
            transparent=False,
        )
        plt.close()

        print(f"Special Case 2: Map for {locality} created!")


if __name__ == "__main__":
    create_and_save_images()
