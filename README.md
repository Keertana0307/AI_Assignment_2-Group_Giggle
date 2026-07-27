# A* Search Route Optimisation

This project implements the A* Search algorithm to determine the minimum-cost route from Sunway University to five residential locations.

The route is evaluated using a weighted path cost that combines:

- 60% normalised carbon emission
- 40% normalised travel expense

## Project Objective

The objective of this project is to determine an optimal route that:

- Starts at Sunway University
- Visits all five residential locations
- Minimises the total accumulated path cost
- Gives greater priority to reducing carbon emissions
- Considers travel expenses as a secondary factor

The project supports United Nations Sustainable Development Goal 13: Climate Action by assigning a higher weight to carbon emissions during route evaluation.

## Path Cost Formula

The weighted cost of travelling between two connected locations is calculated using:

```text
Path Cost = 0.6(Carbon Emission) + 0.4(Travel Expense)
```

## Optimal Route

The optimal route produced by the A* Search algorithm is:

```text
SunU → Vidhipriya → Wen Li → Hui San → Keertana → Qi Yung
```

The total accumulated weighted path cost is:

```text
1.11854
```

## Repository Structure

```text
project-folder/
│
├── README.md
├── requirements.txt
│
├── colab/
│   └── astar_route_optimisation.ipynb
│
└── vscode/
    └── route_video_visualisation.py
```

The repository is organised as follows:

- `colab/` contains one Google Colab notebook with five executable code sections.
- `vscode/` contains one Python script used to generate the route visualisation video.
- `requirements.txt` contains the external Python libraries required by the video script.
- `README.md` provides instructions for executing the project.

## Google Colab Notebook

The Google Colab notebook contains five code cells or sections:

1. Data and Graph Construction
2. State Representation and Data Structure Design
3. Heuristic Function Design
4. A* Search Core Engine with Goal Test
5. Output and Integration

The cells must be executed in order because later sections depend on variables, classes and functions created in earlier sections.

## How to Execute the Google Colab Notebook

### Method 1: Open from GitHub

1. Open this GitHub repository.
2. Open the `colab` folder.
3. Select `astar_route_optimisation.ipynb`.
4. Download the notebook or open it in Google Colab.
5. In Google Colab, select:

```text
Runtime → Run all
```

6. Wait for all five cells to finish executing.

### Method 2: Upload the Notebook Manually

1. Open Google Colab.
2. Select:

```text
File → Upload notebook
```

3. Upload `astar_route_optimisation.ipynb`.
4. Select:

```text
Runtime → Run all
```

The notebook must be executed from the first cell to the fifth cell. Running the later cells before the earlier cells may produce errors because the required variables and functions may not yet exist.

## Expected Google Colab Output

After all five cells have been executed, the expected result is:

```text
Optimal Route:
SunU → Vidhipriya → Wen Li → Hui San → Keertana → Qi Yung

Visited Nodes:
{'SunU', 'Vidhipriya', 'Wen Li', 'Hui San', 'Keertana', 'Qi Yung'}

Total Cost:
1.11854
```

The order of locations displayed inside `Visited Nodes` may vary because Python sets do not maintain a fixed display order.

## VS Code Route Visualisation Script

The Python file inside the `vscode` folder generates an MP4 video that visualises the final optimal route.

The video shows the following route:

```text
Sunway University
→ Vidhipriya
→ Wen Li
→ Hui San
→ Keertana
→ Qi Yung
```

The script uses:

- OSRM to retrieve the driving route between consecutive locations
- OpenStreetMap as the source of geographical map data
- CARTO to provide the basemap tiles
- Pillow to draw markers, route lines, labels and animation frames
- NumPy to process the video frames
- FFmpeg to encode the frames into an MP4 video

## Software Requirements

The project requires:

- Python 3
- Google Colab
- Visual Studio Code
- Internet connection during the first execution of the video script

## Required Python Libraries

The VS Code script requires the following external libraries:

```text
numpy
requests
Pillow
imageio-ffmpeg
```

Install the libraries using:

```bash
pip install -r requirements.txt
```

Alternatively, install them manually:

```bash
pip install numpy requests Pillow imageio-ffmpeg
```

The `requirements.txt` file should contain:

```text
numpy
requests
Pillow
imageio-ffmpeg
```

## How to Execute the VS Code Script

### Step 1: Download the Repository

Download the repository as a ZIP file and extract it.

Alternatively, clone the repository using:

```bash
git clone [YOUR_GITHUB_REPOSITORY_URL](https://github.com/Keertana0307/AI_Assignment_2-Group_Giggle)
```

Move into the project folder:

```bash
cd YOUR_PROJECT_FOLDER
```

Replace `[YOUR_GITHUB_REPOSITORY_URL](https://github.com/Keertana0307/AI_Assignment_2-Group_Giggle)` and `AI_Assignment_2-Group_Giggle` with the actual repository information.

### Step 2: Open the Project in Visual Studio Code

1. Open Visual Studio Code.
2. Select:

```text
File → Open Folder
```

3. Select the downloaded project folder.
4. Open:

```text
vscode/route_video_visualisation.py
```

### Step 3: Select the Python Interpreter

1. Press `Ctrl + Shift + P`.
2. Search for:

```text
Python: Select Interpreter
```

3. Select an installed Python 3 interpreter.

### Step 4: Install the Required Libraries

Open the VS Code terminal and run:

```bash
pip install -r requirements.txt
```

Alternatively, run:

```bash
pip install numpy requests Pillow imageio-ffmpeg
```

### Step 5: Run the Video Script

From the project root folder, run:

```bash
python vscode/route_video_visualisation.py
```

When the terminal is already inside the `vscode` folder, run:

```bash
python route_video_visualisation.py
```

## Generated Video Output

After successful execution, the script generates:

```text
sunway_optimal_route.mp4
```

The video is saved in the current working directory used by the terminal.

The script also creates a cache folder:

```text
map_cache/
```

The `map_cache` folder stores:

- Downloaded CARTO map tiles
- OSRM route coordinates
- Cached route information

The cache prevents the same route and map data from being downloaded again during later executions.

The generated MP4 file and `map_cache` folder are runtime outputs and do not need to be uploaded to the GitHub repository.

## Internet Connection

An internet connection is required during the first execution of the video script because the program retrieves:

- Driving-route coordinates from OSRM
- Basemap tiles from CARTO and OpenStreetMap

When the required data is already stored in `map_cache`, the program can reuse the cached information during later executions.

## Goal Test

The A* Search algorithm terminates when all six graph nodes have been visited:

- Sunway University
- Vidhipriya
- Wen Li
- Hui San
- Keertana
- Qi Yung

The goal-test condition used in the implementation is:

```python
current.visited_set == set(nodes)
```

When this condition evaluates to `True`, the algorithm returns the completed state containing the optimal route and accumulated path cost.

## Technologies Used

- Python
- Google Colab
- Visual Studio Code
- A* Search algorithm
- NumPy
- Requests
- Pillow
- FFmpeg
- OSRM
- OpenStreetMap
- CARTO

## Sustainability Contribution

This project supports United Nations Sustainable Development Goal 13: Climate Action by prioritising lower-carbon travel routes.

Carbon emissions contribute 60% of the weighted path cost, encouraging the A* Search algorithm to select routes with a lower environmental impact while still considering travel expenses.

## Limitations

The current implementation is based on predefined graph connections and static path costs. It does not automatically account for changing real-world conditions such as:

- Traffic congestion
- Road closures
- Fuel-price changes
- Weather conditions
- Changes in travel expenses

The heuristic function also considers only the minimum edge cost to an unvisited neighbouring node. Therefore, it provides a simple estimate rather than a complete estimate of the cost required to visit all remaining locations.

## Privacy Notice

The VS Code video script contains the latitude and longitude of residential locations. Exact residential coordinates should be anonymised, removed or replaced with nearby public landmarks before making the repository publicly accessible.
