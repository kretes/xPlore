# xPlore - find hiking/biking/walking places that you've never been around!

Ever wondered 'I know my city very well, I've been everywhere', or 'I've been biking through this district for ages, I visited every corner there'.

Now you can use data to verify that - and most interestingly - fill in the missing gaps!

This project uses your Location History (exported from Google) and a configured area to find a places that you've never been in.
It as well uses Google API to select points that lays on roads, as this is the best approximation of a 'publicly accessible point' that I found.

This is how it looks like for me on a city-scale (This shows all the places that I've never been closer than 300 meters from - in the circle of 9 km around my place)

You can as well think of it macro-scale. This shows the places in Poland I've never been closer than 30 kilometers:


## How to use it

This is a Python project that is executed in the notebook and the final map is displayed using Folium lib.

To run it you need to checkout THIS repository, and run the notebook `where_have_I_not_been.ipynb`.

The project has some non-standard dependencies. I run it using a docker stack [minimal-notebook](https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-minimal-notebook)
and install dependencies `pip install pandas more-itertools scikit-learn geopy haversine folium`

To run from scratch it requires a Google Cloud API Key that you need to provide. There is some free usage for this API that I've always relied on personally. See [Google API pricing](https://developers.google.com/maps/documentation/roads/usage-and-billing).

## Configuration

The notebook contains the following cell with configuration, so that you can taylor it for your own need:

```python
DATA_DIR = "/home/jovyan/work/data" # a dir where it will store data
N_POINTS_TO_SHOW = 100 # limit on the number of points shown on the final map
MAX_REQUESTS=100 # maximum number of requests to Google API that will be issued at once (this is to prevent from accidentally requesting too much)
GRID_SPACING_M = 1000 # spacing in meters that will be used - the lower - the more detailed map will be constructed (but higher the usage of Google API)
CENTER_POINT = (51.945969, 19.535312) # Lat-long coordinates of a center point to be used
RADIUS_SIZE_KM = 5 # Radius of the circle around the center point (in kilometers)
```

## Limitations

This is a side project I wrote for fun, and it might have some bugs.

### Approximations
Furthermore, given large amounts of data to process (in my case I had > 1 million unique data points in my history) - There are some approximations in the implementation. 
For example I do a knn in euclidean distance directly using lat-lon coordinates first and only then I'm doing the real geodesic distance to determine which point is closest to which.

### Publicly accessible places - False Positives, False Negatives

Some of the points the tool might generate can be in a private space. I didn't find a way to determine if a place is publicly available or not. If you know a way - let me know!
The way to mitigate that is - one can create a file `[excluded_from_exploration.json](data%2Fexcluded_from_exploration.json)` in the data_dir, where one can override the tool to omit such places.
There are 3 things to specify:
 `private_points` - a list of points that should be treated as private
 `private_areas` - a list of areas (2 points from the corners) that should be treated as private
 `manually_visited_areas` - a list of areas (2 points from the corners) that should be treated as already visited (sometimes you miss some data in your location history but you know you were there or simply don't want to go there)

Forests/Nature areas.
Google Roads API is usually not returning paths/trails in nature. that's why some areas might not be selected by this tool. That's a pity but again I don't know of any datasource that could help here.

## Disclaimer

THIS SOFTWARE IS PROVIDED AS-IS. NO WARRANTY PROVIDED, THE AUTHORS AREN'T LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY ARISING FROM THE USE OF THE SOFTWARE.