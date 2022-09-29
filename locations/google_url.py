import re
from urllib.parse import urlsplit, parse_qs


def extract_google_position(item, response):
    for link in response.xpath("//img/@src").extract():
        if link.startswith("https://maps.googleapis.com/maps/api/staticmap"):
            item["lat"], item["lon"] = url_to_coords(link)
            return
    for link in response.xpath("//iframe/@src").getall():
        if link.startswith("https://www.google.com/maps/embed?pb="):
            item["lat"], item["lon"] = url_to_coords(link)
            return
    for link in response.xpath("//a[contains(@href, 'google')]/@href").getall():
        if link.startswith("https://www.google.com/maps/dir") or link.startswith(
            "https://www.google.com/maps/place/"
        ):
            item["lat"], item["lon"] = url_to_coords(link)
            return


def url_to_coords(url: str) -> (float, float):
    def get_query_param(link, query_param):
        parsed_link = urlsplit(link)
        queries = parse_qs(parsed_link.query)
        return queries.get(query_param, [])

    url = url.replace("google.co.uk", "google.com")

    if match := re.search(r"@(-?\d+.\d+),\s?(-?\d+.\d+),\d+z", url):
        return float(match.group(1)), float(match.group(2))

    if url.startswith("https://www.google.com/maps/embed?pb="):
        # https://andrewwhitby.com/2014/09/09/google-maps-new-embed-format/
        params = url[38:].split("!")
        maps_keys = {}
        for i in range(0, len(params)):
            splits = params[i].split("d")
            if len(splits) == 2:
                maps_keys[splits[0]] = splits[1]
        lat_index = lon_index = None
        if maps_keys.keys() == {"1", "2", "3"}:
            lon_index = "2"
            lat_index = "3"
        if maps_keys.keys() == {"1", "2"}:
            lon_index = "2"
            lat_index = "1"
        if lat_index and lon_index:
            return float(maps_keys[lat_index]), float(maps_keys[lon_index])
    elif url.startswith("https://maps.googleapis.com/maps/api/staticmap"):
        # find the first marker location, or the map center
        for markers in get_query_param(url, "markers"):
            for val in markers.split("|"):
                if "," in val:
                    lat, lon = map(float, val.split(","))
                    return lat, lon
        for ll in get_query_param(url, "center"):
            lat, lon = ll.split(",")
            return float(lat), float(lon)
    elif url.startswith("https://www.google.com/maps/dir/"):
        lat, lon = url.split("/")[6].split(",")
        return float(lat.strip()), float(lon.strip())
    elif url.startswith("https://www.google.com/maps/place/"):
        lat, lon = url.split("/")[5].split(",")
        return float(lat.strip()), float(lon.strip())

    if "/maps.google.com/" in url:
        for ll in get_query_param(url, "ll"):
            lat, lon = ll.split(",")
            return float(lat), float(lon)

    return None, None
