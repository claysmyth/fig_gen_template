# fig_gen_template
An opinionated template on organizing data and jupyter notebooks for generating and formatting multi-panel scientific figures, entirely programmatically. 

## Structure
The template suggests the following structure:

- `plotting_config.yaml`: default plotting configuration parameters
- `fig_1/`: example figure
    - `data.csv`: example data. As CSV (or parquet) file or directory of csv (or parquet) files
    - `fig_1A.ipynb`: example figure generation notebook
    - `fig_1A.svg`: example figure output
    - `fig_1B.ipynb`: example figure generation notebook
    - `fig_1B.svg`: example figure output
    - `composite_fig.ipynb`: example notebook for generating the composite figure, with all relevant subpanels (A, B, C, etc.)
    - `composite_fig.svg`: example composite figure output
    - `composite_fig.png`: example composite figure output, with transparent background

The data for generating the figure should be stored in a directory, and the path to this directory should be provided to the figure generation notebook as an input argument. Each subpanel should have its own dedicated notebook, which can be run independently of the others. Ideally, minimal data processing is done in these notebooks, and the data is saved in a format that is easy to load into the notebook, as close to it's final format as possible. The individual subplanel (or subplot) notebooks can generate plots using any desired plotting library, but should ultimately save the output in SVG format. Other languages (e.g. R, Matlab, etc.) can be used to generate subpanels, as long as the output is in SVG format.

The composite figure notebook should collect all of the individual subpanels (as SVG files) into a single figure, and manage the formatting of the figure (e.g. size, aspect ratio, etc.) using svgutils (https://svgutils.readthedocs.io/en/latest/). It should also save the output in SVG and PNG format. 

Why the focus on SVG? SVG files are vector graphics that can be scaled without loss of quality, making them ideal for scientific figures that may need to be resized. They can also be easily edited and manipulated programmatically using tools like svgutils. Additionally, SVGs support transparency and can be converted to other formats like PNG while maintaining high quality. SVGs are viewable in web browsers, which can be useful for debugging.

Plotting configuration parameters are defined globally in `plotting_config.yaml`. These parameters are imported into each notebook, and can be overridden as needed on a per-figure basis. Plotting helper functions can be placed in `utils.py` and will be automatically imported into each notebook. Example plotting helper functions may include svg to png conversion, adding significance bars to bar plots, setting up matplotlib with desired plotting style, etc...


## Installation of necessary dependencies from source (as in, from within the cloned repo)

Ideally use python version <= 3.12.
Note: brew is for MacOS.

```bash
pip install -e .
```

with optional visualization dependencies:

```bash
pip install -e ".[viz]"
```

If using playwright to convert SVGs to PNGs, then proceed with playwrite installation:

```bash
playwright install
```

## Example use-case

Inside the `fig_example` directory, run the following jupyter notebooks to see an example of how to generate a multi-panel figure using plotly, matplotlib, and svgutils:

- `panel_A_gen.ipynb`: generates subfigure/panel A
- `panel_B_C_gen.ipynb`: generates subfigures/panels B and C
- `composite_figure_gen.ipynb`: generates the composite figure and converts the results SVG to PNG.


## Recommended plotting libraries

Dataframing: polars (pandas is ok too)

Flowcharts: mermaid or graphviz

Python plotting libraries: matplotlib (acquarel for styling), seaborn, plotly, plotly-express, altair

Tables: great_tables (However, ammendments need to be made to the _export.py script to save tables as SVGs, as of Nov. 2024. Talk to Clay about getting this code.)
