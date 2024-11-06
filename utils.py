import xml.etree.ElementTree as ET
import os
from playwright.async_api import async_playwright
import yaml
import re
import matplotlib.pyplot as plt


def load_plotting_config(config_path='plotting_config.yaml'):
    """
    Load plotting configuration from YAML file.
    
    Parameters
    ----------
    config_path : str, optional
        Path to the YAML configuration file. Defaults to 'plotting_config.yaml'
        
    Returns
    -------
    dict
        Dictionary containing plotting configuration parameters
    """
    # Try multiple common locations for the config file
    search_paths = [
        config_path,
        os.path.join(os.path.dirname(__file__), config_path),
        os.path.join(os.path.dirname(__file__), '..', config_path),
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
            return config
            
    raise FileNotFoundError(f"Could not find plotting config file. Searched in: {', '.join(search_paths)}")



def setup_matplotlib_params(config: dict) -> None:
    """
    Configure matplotlib parameters based on the plotting configuration.
    
    Parameters
    ----------
    config : dict
        Dictionary containing plotting configuration parameters loaded from YAML
    """
    
    # Font settings
    plt.rcParams['font.family'] = config['font_family']
    plt.rcParams['axes.labelsize'] = config['axis_label_size']
    plt.rcParams['xtick.labelsize'] = config['tick_label_size']
    plt.rcParams['ytick.labelsize'] = config['tick_label_size']
    
    # Legend settings
    plt.rcParams['legend.fontsize'] = config['legend_font_size']
    plt.rcParams['legend.markerscale'] = config['legend_marker_size'] / config['marker_size']
    
    # Figure settings
    plt.rcParams['figure.dpi'] = config['dpi']
    plt.rcParams['savefig.dpi'] = config['dpi']
    
    # Line and marker settings
    plt.rcParams['lines.linewidth'] = config['line_width']
    plt.rcParams['lines.markersize'] = config['marker_size']
    
    # Grid settings
    plt.rcParams['grid.alpha'] = config['grid_alpha']
    
    # Figure margins
    plt.rcParams['figure.subplot.left'] = config['figure_margins']['left']
    plt.rcParams['figure.subplot.right'] = config['figure_margins']['right']
    plt.rcParams['figure.subplot.top'] = config['figure_margins']['top']
    plt.rcParams['figure.subplot.bottom'] = config['figure_margins']['bottom']
    
    # Color settings
    plt.rcParams['axes.prop_cycle'] = plt.cycler('color', config['categorical_colors'])
    
    # Additional common settings for scientific figures
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.linestyle'] = ':'


def get_mpl_dimensions(width, height, plotting_config):
    """
    Get the dimensions of a matplotlib figure, scaled by the config parameters.
    Width and height are specified in pixels.
    """
    dpi = plotting_config['dpi']
    scale_x = plotting_config['mpl_x_scale_factor']
    scale_y = plotting_config['mpl_y_scale_factor']
    return (width * scale_x / dpi, height * scale_y / dpi)


async def convert_svg_to_png_playwright_async(svg_path, output_path, device_scale_factor=1, scale_x=1.0, scale_y=1.0):
    # Get SVG dimensions and viewBox
    tree = ET.parse(svg_path)
    root = tree.getroot()
    width = int(float(root.get('width').replace('px', '')))
    height = int(float(root.get('height').replace('px', '')))
    
    # Get viewBox if it exists, otherwise use width/height
    viewbox = root.get('viewBox')
    if viewbox:
        _, _, vb_width, vb_height = map(float, viewbox.split())
        width = int(vb_width)
        height = int(vb_height)
    
    # Scale the SVG content by modifying transform attribute and adjust for both x and y shifts
    root.set('transform', f'translate({width * (scale_x - 1)/2},{height * (scale_y - 1)/2}) scale({scale_x},{scale_y})')
    
    # Save modified SVG
    scaled_svg_path = svg_path.replace('.svg', '_scaled.svg')
    tree.write(scaled_svg_path)
    abs_svg_path = os.path.abspath(scaled_svg_path)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={'width': int(width * scale_x), 'height': int(height * scale_y)},
            device_scale_factor=device_scale_factor
        )
        page = await context.new_page()
        await page.goto(f'file://{abs_svg_path}')
        await page.wait_for_timeout(1000)
        
        # Get the SVG element's bounding box
        svg_elem = await page.query_selector('svg')
        bbox = await svg_elem.bounding_box()
        
        await page.screenshot(
            path=output_path,
            clip={'x': bbox['x'], 'y': bbox['y'], 
                  'width': bbox['width'] * scale_x, 'height': bbox['height'] * scale_y}
        )
        await browser.close()
        
        # Clean up temporary scaled SVG
        os.remove(scaled_svg_path)


## Deprecated functions for trying to resize matplotlib generated svgs

# def convert_units(value, from_unit, to_unit, config):
#     conversion_factor = config['conversions'][from_unit] / config['conversions'][to_unit]
#     return value * conversion_factor

# def convert_svg_size(svg_path, target_units, final_size, config):
#     """
#     Convert SVG dimensions to target units and scale to desired final size.
    
#     Parameters
#     ----------
#     svg_path : str
#         Path to the SVG file
#     target_units : str
#         Target units to convert to (e.g., 'px', 'pt', 'in', 'cm', 'mm')
#     final_size : tuple
#         Desired final size (width, height) in target units
#     config : dict
#         Configuration dictionary containing unit conversion factors
        
#     Returns
#     -------
#     None
#         Modifies the SVG file in place
#     """
#     tree = ET.parse(svg_path)
#     root = tree.getroot()
    
#     # Get current dimensions and units
#     width_str = root.get('width', '0')
#     height_str = root.get('height', '0')
    
#     # Parse dimensions and units
#     current_width = float(width_str.rstrip('abcdefghijklmnopqrstuvwxyz'))
#     current_height = float(height_str.rstrip('abcdefghijklmnopqrstuvwxyz'))
#     current_units = width_str[len(str(current_width)):] or 'px'
    
#     # Convert to target units and calculate scale
#     width_in_target = convert_units(current_width, current_units, target_units, config)
#     height_in_target = convert_units(current_height, current_units, target_units, config)
#     scale = (final_size[0] / width_in_target, final_size[1] / height_in_target)
    
#     # Update SVG dimensions
#     root.set('width', f"{final_size[0]}{target_units}")
#     root.set('height', f"{final_size[1]}{target_units}") 
#     root.set('viewBox', f"0 0 {final_size[0]} {final_size[1]}")
    
#     # Scale content
#     if (g := root.find('.//{http://www.w3.org/1999/xlink}g')):
#         g.set('transform', f'scale({scale[0]},{scale[1]})')
    
#     tree.write(svg_path, encoding='utf-8', xml_declaration=True)


# def infer_scale_factor(unit, conversion_dict):
#     """Infer the scaling factor based on the target unit being pixels."""
#     if unit in conversion_dict:
#         return conversion_dict['px'] / conversion_dict[unit]
#     else:
#         raise ValueError(f"Unknown unit: {unit}")


# def modify_svg_dimensions(filepath, target_unit='px', conversion_dict=None, desired_width_px=None, desired_height_px=None):
#     # Read the SVG content from the file
#     with open(filepath, 'r') as file:
#         svg_content = file.read()
    
#     # Extract the original width and height, and try to identify their units
#     width_match = re.search(r'width="([\d.]+)([a-zA-Z]*)"', svg_content)
#     height_match = re.search(r'height="([\d.]+)([a-zA-Z]*)"', svg_content)
    
#     if not (width_match and height_match):
#         raise ValueError("SVG does not contain width and height attributes with recognized units.")
    
#     # Original dimensions and units
#     original_width = float(width_match.group(1))
#     original_height = float(height_match.group(1))
#     original_unit = width_match.group(2) or 'px'  # Default to pixels if no unit is specified

#     # Infer scale factor based on the original unit
#     scale_factor = infer_scale_factor(original_unit, conversion_dict)
    
#     # Calculate new dimensions in pixels if not provided
#     if desired_width_px is None:
#         desired_width_px = int(original_width * scale_factor)
#     if desired_height_px is None:
#         desired_height_px = int(original_height * scale_factor)
    
#     # Modify the SVG content with new dimensions and units in pixels
#     svg_content = re.sub(r'width="[\d.]+[a-zA-Z]*"', f'width="{desired_width_px}{target_unit}"', svg_content)
#     svg_content = re.sub(r'height="[\d.]+[a-zA-Z]*"', f'height="{desired_height_px}{target_unit}"', svg_content)
    
#     # Apply scaling to the viewBox dimensions
#     viewbox_match = re.search(r'viewBox="([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)"', svg_content)
#     if viewbox_match:
#         x_min, y_min, width_original, height_original = map(float, viewbox_match.groups())
#         new_width_viewbox = width_original * scale_factor
#         new_height_viewbox = height_original * scale_factor
#         svg_content = re.sub(
#             r'viewBox="[\d.]+ [\d.]+ [\d.]+ [\d.]+',
#             f'viewBox="0 0 {new_width_viewbox} {new_height_viewbox}',
#             svg_content
#         )
#     else:
#         # If there's no viewBox, add one with the scaled dimensions
#         svg_content = re.sub(
#             r'(<svg[^>]*>)',
#             r'\1<viewBox="0 0 {} {}">'.format(desired_width_px, desired_height_px),
#             svg_content,
#             count=1
#         )
    
#     # Insert new encoding header if necessary
#     svg_content = re.sub(r'encoding="utf-8"', 'encoding="ASCII"', svg_content)

#     # Save the modified SVG content back to the file
#     with open(filepath, 'w') as file:
#         file.write(svg_content)

# def reset_svg_dimensions(svg_path: str, dimensions: tuple, units: str = 'px') -> None:
#     """
#     Reset the width and height attributes of an SVG file.

#     Parameters
#     ----------
#     svg_path : str
#         Path to the SVG file
#     dimensions : tuple
#         Desired (width, height) dimensions
#     units : str, optional
#         Units for the dimensions (default: 'px')
        
#     Returns
#     -------
#     None
#         Modifies the SVG file in place
#     """
#     tree = ET.parse(svg_path)
#     root = tree.getroot()
    
#     # Set new width and height
#     root.set('width', f"{dimensions[0]}{units}")
#     root.set('height', f"{dimensions[1]}{units}")
    
#     # Update viewBox to match new dimensions
#     root.set('viewBox', f"0 0 {dimensions[0]} {dimensions[1]}")
    
#     # Save modified SVG
#     tree.write(svg_path, encoding='utf-8', xml_declaration=True)

# def resize_svg(
#     svg_path: str,
#     desired_width: float,
#     desired_height: float,
#     target_units: str = 'px',
#     maintain_aspect_ratio: bool = False
# ) -> None:
#     """
#     Resize an SVG and all its components to specified dimensions.
    
#     Parameters
#     ----------
#     svg_path : str
#         Path to the SVG file
#     desired_width : float
#         Desired width in target units
#     desired_height : float
#         Desired height in target units
#     target_units : str, optional
#         Target units for dimensions (default: 'px')
#     maintain_aspect_ratio : bool, optional
#         If True, maintains aspect ratio using the smaller scaling factor
        
#     Returns
#     -------
#     None
#         Modifies the SVG file in place
#     """
#     # Read the SVG content
#     with open(svg_path, 'r') as file:
#         content = file.read()
    
#     # Extract current dimensions and units
#     width_match = re.search(r'width="([0-9.]+)([a-z]*)"', content)
#     height_match = re.search(r'height="([0-9.]+)([a-z]*)"', content)
#     viewbox_match = re.search(r'viewBox="([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)"', content)
    
#     if not (width_match and height_match):
#         raise ValueError("Could not find width and height attributes in SVG")
    
#     # Get current dimensions
#     current_width = float(width_match.group(1))
#     current_height = float(height_match.group(1))
#     current_width_unit = width_match.group(2) or 'px'
#     current_height_unit = height_match.group(2) or 'px'
    
#     # Calculate scale factors
#     scale_x = desired_width / current_width
#     scale_y = desired_height / current_height
    
#     if maintain_aspect_ratio:
#         scale = min(scale_x, scale_y)
#         scale_x = scale_y = scale
#         desired_width = current_width * scale
#         desired_height = current_height * scale
    
#     # Update main SVG attributes
#     content = re.sub(
#         r'width="[^"]*"',
#         f'width="{desired_width}{target_units}"',
#         content
#     )
#     content = re.sub(
#         r'height="[^"]*"',
#         f'height="{desired_height}{target_units}"',
#         content
#     )
    
#     # Update viewBox if it exists
#     if viewbox_match:
#         vb_x, vb_y, vb_width, vb_height = map(float, viewbox_match.groups())
#         new_vb_width = vb_width * scale_x
#         new_vb_height = vb_height * scale_y
#         content = re.sub(
#             r'viewBox="[^"]*"',
#             f'viewBox="0 0 {new_vb_width} {new_vb_height}"',
#             content
#         )
#     else:
#         # Add viewBox if it doesn't exist
#         content = content.replace(
#             '<svg',
#             f'<svg viewBox="0 0 {desired_width} {desired_height}"'
#         )
    
#     # Scale transform attributes
#     def scale_transform(match):
#         transform = match.group(1)
#         # Handle different transform types
#         if 'scale' in transform:
#             # Update existing scale
#             transform = re.sub(
#                 r'scale\([^)]+\)',
#                 f'scale({scale_x},{scale_y})',
#                 transform
#             )
#         else:
#             # Add scale to existing transform
#             transform += f' scale({scale_x},{scale_y})'
#         return f'transform="{transform}"'
    
#     content = re.sub(r'transform="([^"]*)"', scale_transform, content)
    
#     # Update any explicit position coordinates
#     def scale_coords(match):
#         x = float(match.group(1)) * scale_x
#         y = float(match.group(2)) * scale_y
#         return f'x="{x}" y="{y}"'
    
#     content = re.sub(r'x="([0-9.]+)"\s*y="([0-9.]+)"', scale_coords, content)
    
#     # Convert all units to target units
#     for unit in ['pt', 'px', 'in', 'cm', 'mm']:
#         content = content.replace(f'"{unit}"', f'"{target_units}"')
    
#     # Write modified content back to file
#     with open(svg_path, 'w') as file:
#         file.write(content)