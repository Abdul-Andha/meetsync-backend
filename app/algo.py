import requests
from shapely.geometry import Polygon, MultiPolygon, Point
from dotenv import dotenv_values
from custom_errors import UnexpectedError

config = dotenv_values(".env")


def getIsochrones(startingPoints, times, transportModes):
    n = len(startingPoints)
    if len(times) != n or len(transportModes) != n:
        raise ValueError("All input lists must have the same length")

    URL = "https://api.traveltimeapp.com/v4/time-map/fast"
    headers = {
        "X-API-Key": config["TRAVEL_TIME_API_KEY"],
        "X-Application-Id": config["TRAVEL_TIME_APPLICATION_ID"],
        "Content-Type": "application/json",
    }

    searches = []
    for i in range(n):
        if times[i] > 180:
            raise ValueError("Travel time must be less than 3 hours (180 minutes)")
        search = {
            "id": f"isochrone-{i}",
            "travel_time": times[i] * 60,
            "coords": {"lng": startingPoints[i][1], "lat": startingPoints[i][0]},
            "transportation": {"type": transportModes[i]},
            "arrival_time_period": "weekday_morning",
            "level_of_detail": {"scale_type": "simple", "level": "medium"},
            "no_holes": False,
        }
        searches.append(search)

    body = {
        "arrival_searches": {
            "one_to_many": searches,
        }
    }

    response = requests.post(URL, json=body, headers=headers)
    data = response.json()

    multiPolygons = []
    for i in range(n):
        shapes = data["results"][i]["shapes"]
        polygons = []
        for shape in shapes:
            shell = [(point["lng"], point["lat"]) for point in shape["shell"]]
            holes = [
                [(point["lng"], point["lat"]) for point in hole]
                for hole in shape.get("holes", [])
            ]
            polygons.append(Polygon(shell, holes))
        multiPolygons.append(MultiPolygon(polygons))

    return multiPolygons


def getEnclosingCircle(polygon):
    if isinstance(polygon, MultiPolygon):
        polygon = max(polygon.geoms, key=lambda p: p.area)

    center = polygon.centroid
    maxDistDegree = max(center.distance(Point(p)) for p in polygon.exterior.coords)
    radius = maxDistDegree * 111320  # approx meters / degree
    return center, radius


def getPlaces(polygon, center, radius):
    URL = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "X-Goog-Api-Key": config["GOOG_API_KEY"],
        "Content-Type": "application/json",
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }
    body = {
        "includedTypes": ["restaurant"],
        "maxResultCount": 10,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": center.y, "longitude": center.x},
                "radius": radius,
            }
        },
    }
    response = requests.post(URL, json=body, headers=headers)
    data = response.json()
    places = data["places"]
    filteredPlaces = []
    for place in places:
        point = Point(place["location"]["longitude"], place["location"]["latitude"])
        if polygon.contains(point):
            filteredPlaces.append(place)

    return filteredPlaces


def getOverlap(polygons):
    if len(polygons) == 0:
        return None

    overlap = polygons[0]
    for poly in polygons[1:]:
        overlap = overlap.intersection(poly)

    return overlap


def getGeocodes(addresses: list[str]):
    if len(addresses) == 0:
        raise ValueError("Addresses array can't be empty")

    URL = f"https://api.mapbox.com/search/geocode/v6/batch?access_token={config['MAPBOX_ACCESS_TOKEN']}"
    headers = {"Content-Type": "application/json"}
    body = []

    for address in addresses:
        body.append({"types": ["address"], "q": address, "limit": 1})

    response = requests.post(URL, headers=headers, json=body)
    data = response.json()

    if not data or data.get("batch") == None:
        raise UnexpectedError

    geocodes = []
    for i in range(len(data["batch"])):
        if len(data["batch"][i].get("features")) == 0:
            raise ValueError(f"{addresses[i]} did not map to a geocode")

        point = data["batch"][i].get("features")[0].get("geometry").get("coordinates")
        geocodes.append(point)

    return geocodes


"""
TODO: main function that does the following: (does this after availability algo is done and addresses/times/transports are confirmed)
1. takes in hangout_id param
2. finds all hangout_participants that have accepted that hangout and gets their confirmed address, travel time, and mode of transport (error checking) 
3. uses getGeocodes to get everyone's lat/lng
4. uses list of lat/lng, times, and transports to getIsochrones
5. getOvelap of isochrones (error if overlap is empty)
6. getEnclosingCircle of overlap
7. getPlaces in circle and filter out whatevers not in overlap (error if no places found)
8. return list of filteredPlaces (might want to store this in supabase too)
"""
