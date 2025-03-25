import requests
from shapely.geometry import Polygon, MultiPolygon, Point
from dotenv import dotenv_values
from app.custom_errors import InvalidHangout, UnexpectedError, ExternalAPIError
from app.custom_types import HangoutStatus
import app.data_accessor as da

config = dotenv_values(".env")


def getIsochrones(startPoints, times, transportModes):
    """
    Retrieve isochrones for all users

    1. Raise errors if lengths of input lists are not equal
    2. Send POST request to TravelTime API
    3. Return list of MultiPolygons of isochrones
    """

    n = len(startPoints)
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
            "coords": {"lng": startPoints[i][0], "lat": startPoints[i][1]},
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

    try:
        response = requests.post(URL, json=body, headers=headers)
        data = response.json()
        if data.get("results") == None:
            raise ExternalAPIError(
                f"TravelTimeAPI Error {data['error_code']}: {data['description']}"
            )
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

    except Exception as e:
        raise ExternalAPIError(e)

    return multiPolygons


def getEnclosingCircle(polygon):
    """
    Given a polygon, return a circle that encloses it

    1. Returns center and radius of the enclosing circle
    """

    if isinstance(polygon, MultiPolygon):
        polygon = max(polygon.geoms, key=lambda p: p.area)

    center = polygon.centroid
    maxDistDegree = max(center.distance(Point(p)) for p in polygon.exterior.coords)
    radius = maxDistDegree * 111320  # approx meters / degree
    return center, radius


def getPlaces(polygon, center, radius):
    """
    Returns places within the polygon

    1. Send POST request to Google Places API to get places within radius of center
    2. Filter out places that are not within the polygon
    3. Return filtered places
    """

    URL = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "X-Goog-Api-Key": config["GOOGLE_API_KEY"],
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

    try:
        response = requests.post(URL, json=body, headers=headers)
        data = response.json()
        if data.status_code != 200:
            raise ExternalAPIError(
                f"GooglePlacesAPI Error {data['error_code']}: {data['error_message']}"
            )
        places = data["places"]
        filteredPlaces = []
        for place in places:
            point = Point(place["location"]["longitude"], place["location"]["latitude"])
            if polygon.contains(point):
                filteredPlaces.append(place)
    except Exception as e:
        raise ExternalAPIError(e)

    return filteredPlaces


def getOverlap(polygons):
    """
    Returns the overlap of multiple polygons
    """

    if len(polygons) == 0:
        return None

    overlap = polygons[0]
    for poly in polygons[1:]:
        overlap = overlap.intersection(poly)

    return overlap


def getGeocodes(addresses: list[str]):
    """
    Returns the geocodes for a list of addresses

    1. Raise error if addresses is empty
    2. Send POST request to Mapbox API
    3. Raise error if any address does not map to a geocode
    4. Return list of geocodes
    """

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
        raise ExternalAPIError(f"MapboxAPI Error {data['code']}: {data['message']}")

    geocodes = []
    for i in range(len(data["batch"])):
        if len(data["batch"][i].get("features")) == 0:
            raise ValueError(f"{addresses[i]} did not map to a geocode")

        point = data["batch"][i].get("features")[0].get("geometry").get("coordinates")
        geocodes.append(point)

    return geocodes


def getAlgoInputs(hangout_id: str):
    """
    Returns the addresses, travel times, and transport modes for all participants in a hangout
    """
    try:
        participants = da.get_hangout_participants(hangout_id)["participants"]

        startAddresses = []
        travelTimes = []
        transportModes = []
        for participant in participants:
            startAddresses.append(participant["start_address"])
            travelTimes.append(participant["travel_time"])
            transportModes.append(participant["transport"])

    except Exception as e:
        raise UnexpectedError(e)

    return startAddresses, travelTimes, transportModes


def getRecommendations(hangout_id: int):
    """
    Returns a list of recommended places for the hangout

    1. Raise error if hangout_id is falsey
    2. Get hangout from supabase
        a. Raise error if hangout status is not determining-location
    3. Get addresses, travel times, and transport modes for all participants
        a. Raise error if lengths of input lists are not equal
    4. Get geocodes for all addresses
    5. Get isochrones for all participants
    6. Get overlap of isochrones
        a. Raise error if no overlap
    7. Get enclosing circle of overlap
    8. Get places within circle and filter out places not in overlap
        a. Raise error if no places found
    9. Return list of filtered places
    """
    if hangout_id is None or hangout_id == "":
        raise InvalidHangout("Hangout ID can not null")

    try:
        hangout = da.get_hangout(hangout_id)["hangout"]
        if hangout["status"] != HangoutStatus.DETERMINING_LOCATION:
            raise ValueError(
                f"Hangout status must be determining-location not {hangout['status']}"
            )

        startAddresses, travelTimes, transportModes = getAlgoInputs(hangout_id)
        if len(startAddresses) != len(travelTimes) or len(startAddresses) != len(
            transportModes
        ):
            raise ValueError(
                "Lengths of startAddresses, travelTimes, and transportModes must be equal"
            )
        startPoints = getGeocodes(startAddresses)

        isochrones = getIsochrones(startPoints, travelTimes, transportModes)
        overlap = getOverlap(isochrones)
        if overlap is None or overlap.is_empty:
            raise ValueError("No overlap between isochrones")

        center, radius = getEnclosingCircle(overlap)
        filteredPlaces = getPlaces(overlap, center, radius)
        if len(filteredPlaces) == 0:
            raise ValueError("No places found within overlap")

        return {"status": 200, "places": filteredPlaces}

    except Exception as e:
        raise UnexpectedError(e)
