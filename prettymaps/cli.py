import sys
from pathlib import Path

import click
import PIL
from matplotlib import cm as colormaps
from matplotlib import pyplot as plt

from .draw import plot

cm = 1 / 2.54  # cm, in inches

dimensions_inches = {
    "square": (50 * cm, 50 * cm),
    "A3": (29.7 * cm, 42.0 * cm),
    "A2": (42.0 * cm, 59.4 * cm),
    "A1": (59.4 * cm, 84.1 * cm),
    "A0": (84.1 * cm, 118.8 * cm),
    "70": (70*cm, 70*cm)
}


def make_theme(building_palette, background_color, bw=False):
    return {
        "background": {
            "fc": "#fff" if bw else background_color,
            "ec": "#fff" if bw else "#dadbc1",
            "hatch": "......",
            "zorder": -1,
        },
        "perimeter": {"fill": False, "lw": 0.1 if bw else 0, "zorder": 0},
        "green": {
            "fc": "#ffffff" if bw else "#8BB174",
            "ec": "#000" if bw else "#2F3737",
            "hatch_c": "#ffffff" if bw else "#A7C497",
            "hatch": "......",
            "lw": 0.2 if bw else 1,
            "zorder": 1,
            "alpha": 0.5,
        },
        "garden": {
            "fc": "#ffffff" if bw else "#72C07A",
            "ec": "#000000" if bw else "#64a38d",
            "lw": 0,
            "zorder": 1,
            "hatch": "......",
        },
        "water": {
            "fc": "#ffffff" if bw else "#a8e1e6",
            "ec": "#000000" if bw else "#2F3737",
            "lw": 1,
            "zorder": 3,
        },
        "streets": {
            "fc": "#ffffff" if bw else "#2F3737",
            "ec": "#000000" if bw else "#475657",
            "alpha": 1,
            "lw": 0,
            "zorder": 4,
        },
        "pedestrian": {
            "fc": "#ffffff" if bw else "#2F3737",
            "ec": "#000000" if bw else "#475657",
            "alpha": 1,
            "lw": 0,
            "zorder": 4,
        },
        "building": {
            "palette": building_palette if not bw else ["#ffffff"],
            "ec": "#000000" if bw else "#2F3737",
            "lw": 0.5,
            "zorder": 5,
        },
        "parking": {
            "palette": building_palette if not bw else ["#ffffff"],
            "ec": "#000000" if bw else "#2F3737",
            "lw": 0.6 if bw else 0.5,
            "zorder": 5,
        },
        "forest": {
            "fc": "#ffffff" if bw else "#8BB174",
            "ec": "#000000" if bw else "#2F3737",
            "hatch_c": "#ffffff" if bw else "#A7C497",
            "hatch": "......",
            "lw": 1,
            "zorder": 1,
            "alpha": 0.5,
        },
        "park": {
            "fc": "#ffffff" if bw else "#AAD897",
            "ec": "#000000" if bw else "#8bc49e",
            "lw": 0,
            "zorder": 1,
            "hatch": "......",
        },
        "wetland": {
            "fc": "#ffffff" if bw else "#D2D68D",
            "ec": "#000000" if bw else "#AEB441",
            "lw": 0,
            "zorder": 3,
            "hatch": "......",
        },
        "beach": {
            "fc": "#ffffff" if bw else "#e3da8d",
            "ec": "#000000" if bw else "#AEB441",
            "lw": 0,
            "zorder": 3,
            "hatch": "",
        },
    }


def generate_layers(circle, river_overflow):
    return {
        "perimeter": {},
        "streets": {
            "custom_filter": '["highway"~"motorway|trunk|primary|secondary|tertiary|residential|service|unclassified|pedestrian|footway"]',
            "width": {
                "motorway": 5,
                "trunk": 5,
                "primary": 4.5,
                "secondary": 4,
                "tertiary": 3.5,
                "residential": 3,
                "service": 2,
                "unclassified": 2,
                "pedestrian": 2,
                "footway": 1,
            },
            "circle": circle,
        },
        "park": {
            "tags": {
                "leisure": "park",
                "landuse": "golf_course",
                "landuse": "meadow",
                "leisure": "nature_reserve",
                "boundary": "protected_area",
                "place": "square",
                "natural": "grassland",
                "landuse": "military",
                "amenity": "hospital",
            }
        },
        "building": {
            "tags": {"building": True, "landuse": "construction"},
            "union": False,
            "circle": circle,
        },
        "water": {
            "tags": {"natural": ["water", "bay", "river", "stream", "waterway"]},
            "circle": not circle if river_overflow else circle,
            "dilate": 100 if river_overflow else 0,
        },
        "green": {
            "tags": {
                "landuse": "grass",
                "natural": ["island", "wood"],
                "leisure": "park",
            },
            "circle": circle,
        },
        "forest": {"tags": {"landuse": "forest"}, "circle": circle},
        "parking": {
            "tags": {
                "amenity": "parking",
                "highway": "pedestrian",
                "man_made": "pier",
            },
            "circle": circle,
        },
        "pedestrian": {"tags": {"area:highway": "pedestrian"}},
        "wetland": {"tags": {"natural": "wetland", "natural": "scrub"}},
        "beach": {"tags": {"natural": "beach"}},
        "garden": {"tags": {"leisure": "garden"}},
    }


def rgb_to_hex(r, b, g):
    """Convert an RGB color to its hex representation"""
    if not (0 <= r <= 255 or 0 <= b <= 255 or 0 <= g <= 255):
        raise ValueError("rgb not in range(256)")
    return "#%02x%02x%02x" % (r, b, g)


def colormap_to_palette(colormap_name):
    """Generate a color palette given the name of a matplotlib colormap"""
    palette = []
    cmap = colormaps._colormaps[colormap_name]
    if hasattr(cmap, "_segmentdata"):
        cmap_colors = cmap._segmentdata
        for i in range(len(cmap_colors["blue"])):
            r = int(cmap_colors["red"][i][2] * 255)
            b = int(cmap_colors["blue"][i][2] * 255)
            g = int(cmap_colors["green"][i][2] * 255)
            palette.append(rgb_to_hex(r, g, b))
    elif hasattr(cmap, "colors"):
        for r, g, b in cmap.colors:
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
            palette.append(rgb_to_hex(r, g, b))
    return palette


custom_themes = {
    "old-school": {
        "building_palette": ["#e77f67", "#e15f41", "#f5cd79", "#f19066"],
        "background_color": "#f7d794",
    },
    "default": {
        "building_palette": ["#e77f67", "#e15f41", "#f5cd79", "#f19066"],
        "background_color": "#ffffff",
    },
    "tartan": {
        "building_palette": [
            "#ad2f32",
            "#3b3968",
            "#3b2549",
            "#5a8637",
            "#d69c46",
            "#9f414f",
        ],
        "background_color": "#ffffff",
    },
    # https://kilts.fr/media/catalog/product/cache/1/thumbnail/600x/05e17a266b0e9cc26fb81a2e0bed7e78/r/o/royal_stewart_1_1.jpg
    "royal-stewart": {
        "building_palette": [
            "#E8C2BD",
            "#31060E",
            "#941C36",
            "#BE0E1B",
            "#5F1219",
        ],
        "background_color": "#ffffff",
    },
    "royal-stewart2": {
        "building_palette": ["#AE5D4A", "#97131C", "#31060E", "#B46D70", "#C01523"],
        "background_color": "#ffffff",
    },
    "royal-stewart3": {
        "building_palette": ["#1D1634", "#BE0E1B", "#B46D70", "#E8C2BD", "#943A34"],
        "background_color": "#ffffff",
    },
    "edern": {
        "building_palette": [
            "#217a79",
            "#105965",
            "#074050",
        ],
        "background_color": "#ffffff",
    },
}


def add_margin_on_each_side(img_path, img_dimensions_inches, margin_cm, rgb_color, dpi):
    """Add a margin of argument size in cm to the 4 sides of the image."""
    img = PIL.Image.open(img_path)
    width_px, height_px = img.size
    nb_px_per_cm = int(width_px / (img_dimensions_inches[0] / cm))
    margin_cm_in_px = int(margin_cm * nb_px_per_cm)
    new_width = width_px + 2 * margin_cm_in_px
    new_height = height_px + 2 * margin_cm_in_px
    result = PIL.Image.new(img.mode, (new_width, new_height), rgb_color)
    result.paste(img, (margin_cm_in_px, margin_cm_in_px))
    result.save(img_path, dpi=(dpi, dpi))


def format_autodocumented_title():
    tokens = sys.argv[:]
    ignored_flags = ["--cmd-as-title"]
    ignored_options = ["-o", "--output-dir"]
    cmd_tokens = ["prettymaps"] + tokens[1:]
    for flag in ignored_flags:
        if flag in cmd_tokens:
            cmd_tokens.remove(flag)
    for opt in ignored_options:
        try:
            idx = cmd_tokens.index(opt)
        except ValueError:
            continue
        else:
            cmd_tokens = cmd_tokens[:idx] + cmd_tokens[idx + 2 :]
    location_idx = cmd_tokens.index("--location")
    cmd_tokens[location_idx + 1] = '"' + cmd_tokens[location_idx + 1]
    for i, tok in enumerate(cmd_tokens[location_idx + 2 :], location_idx + 1):
        if tok.startswith("-"):
            break
    cmd_tokens[i] = cmd_tokens[i] + '"'
    return " ".join(cmd_tokens)


@click.command()
@click.option(
    "--location",
    required=True,
    help="The address to geocode and use as the central point around which to get the geometries",
)
@click.option(
    "--radius",
    default=1000,
    type=int,
    help="Radius, in meters, around the provided location",
    show_default=True,
)
@click.option(
    "--circle",
    is_flag=True,
    help="If true, the map will be represented as a circle, and as a square if not.",
    show_default=True,
)
@click.option(
    "--format",
    default="A3",
    type=click.Choice(list(dimensions_inches.keys())),
    help="The output dimenions of the map",
    show_default=True,
)
@click.option(
    "--theme",
    default="default",
    type=click.Choice(list(custom_themes.keys()) + list(colormaps._colormaps)),
    help="The color theme to use, chosen among the hardcoded list of themes or matplotlib colormaps (see https://matplotlib.org/stable/gallery/color/colormap_reference.html for the complete list)",
    show_default=True,
)
@click.option(
    "--vertical",
    is_flag=True,
    help="Orient the generated map vertically if true",
    show_default=True,
)
@click.option(
    "--river-overflow",
    is_flag=True,
    help="Let rivers overflow from the map if true",
    show_default=True,
)
@click.option(
    "--background-color",
    default="#ffffff",
    help="The HTML background color",
    show_default=True,
)
@click.option(
    "--margins-mm",
    default=0,
    type=int,
    help="The margin size, in mm, to place around the map. Useful for print jobs..",
    show_default=True,
)
@click.option(
    "--scaling-factor",
    default=1,
    type=int,
    help="The scaling factor applied on the final generated image.",
    show_default=True,
)
@click.option(
    "--padding",
    default=100,
    type=int,
    help="The padding to be applied around the map.",
    show_default=True,
)
@click.option(
    "--cmd-as-title",
    is_flag=True,
    help="If true, set the map title as the prettymaps CLI command used to generate it",
    show_default=True,
)
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=str,
    help="The directory to store the map under",
    show_default=True,
)
@click.option(
    "--dpi",
    default=100,
    type=int,
    help="Number of pixels per inch",
    show_default=True,
)
@click.option(
    "--credit/--no-credit",
    default=True,
    is_flag=True,
    help="Show/hide credits",
    show_default=True,
)
@click.option("--bw", is_flag=True, help="Generate a black & white map")
def draw(
    location,
    radius,
    circle,
    cmd_as_title,
    format,
    theme,
    vertical,
    river_overflow,
    background_color,
    margins_mm,
    scaling_factor,
    padding,
    output_dir,
    dpi,
    credit,
    bw,
):
    """Artistic map generation CLI, based on the prettymaps library

    Examples:

      \b
      # generate a map for the argument location
      $ prettymaps --location <address>


      \b
      # generate a circular map
      $ prettymaps --location <address> --circle

      \b
      # generate a circular map with the theme based off the matplotlib colormap Set3
      $ prettymaps --location <address> --circle --theme Set3

      \b
      # Generate a map of the area 2000m around the provided location
      $ prettymaps --location <address> --radius 2000

    """
    default_dpi = plt.rcParams["figure.dpi"]
    dpi_ratio = dpi / default_dpi
    padding *= dpi_ratio
    figsize = tuple([x * scaling_factor for x in dimensions_inches[format]])
    plt.rcParams["figure.dpi"] = dpi

    if not vertical:
        figsize = tuple(reversed(figsize))
    _, ax = plt.subplots(figsize=figsize, constrained_layout=True)

    # Either pick a pre-generated theme or dynamically generate one from a matplotlib
    # colormap name
    if not background_color.startswith("#"):
        background_color = f"#{background_color}"

    themes = {
        name: make_theme(**theme_params, bw=bw)
        for name, theme_params in custom_themes.items()
    }
    if theme in themes:
        theme_params = themes[theme]
    else:
        theme_params = make_theme(
            colormap_to_palette(theme),
            background_color=background_color,
            bw=bw,
        )

    shape = "circle" if circle else "square"
    theme_name = "bw" if bw else theme
    base_filename = (
        location.lower().replace(",", "_").replace(" ", "")
        + f"-{radius}-{format}-{shape}-{theme_name}"
    )
    filename = f"{base_filename}.png"
    if output_dir:
        filename = Path(output_dir) / filename

    plot(
        query=location,
        ax=ax,
        figsize=figsize,
        radius=radius,
        title=format_autodocumented_title() if cmd_as_title else None,
        credit=False if not credit else {"fontfamily": "monospace"},
        layers=generate_layers(circle, river_overflow),
        style=theme_params,
        ratio=figsize[0] / figsize[1],
        preset=None,
        circle=True if circle else False,
        padding=padding,
        save_as=filename,
    )

    # Add margins, for the printer
    if margins_mm:
        add_margin_on_each_side(
            filename,
            img_dimensions_inches=figsize,
            margin_cm=margins_mm / 10,
            rgb_color=(255, 255, 255),
            dpi=dpi,
        )


if __name__ == "__main__":
    draw()
