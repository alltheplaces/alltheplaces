import re
from urllib.parse import parse_qs, urlsplit


def extract_google_position(item, response):
    for link in response.xpath("//img/@src").extract():
        if link.startswith("https://maps.googleapis.com/maps/api/staticmap"):
            item["lat"], item["lon"] = url_to_coords(link)
            return
    for link in response.xpath("//iframe/@src").getall():
        if link.startswith("https://www.google.com/maps/embed"):
            item["lat"], item["lon"] = url_to_coords(link)
            return
    for link in response.xpath("//a[contains(@href, 'google')][contains(@href, 'maps')]/@href").getall():
        item["lat"], item["lon"] = url_to_coords(link)
        return
    for link in response.xpath("//a[contains(@href, 'maps.apple.com')]/@href").getall():
        item["lat"], item["lon"] = url_to_coords(link)
        return


def url_to_coords(url: str) -> (float, float):  # noqa: C901
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
    elif url.startswith("https://www.google.com/maps/embed/v1/place"):
        for q in get_query_param(url, "q"):
            q = q.split(",")
            if len(q) == 2:
                return float(q[0]), float(q[1])
    elif url.startswith("https://maps.googleapis.com/maps/api/staticmap"):
        # find the first marker location, or the map center
        for markers in get_query_param(url, "markers"):
            for val in markers.split("|"):
                if m := re.match(r"(-?\d+.\d+),(-?\d+.\d+)", val):
                    lat, lon = float(m.group(1)), float(m.group(2))
                    return lat, lon
        for ll in get_query_param(url, "center"):
            lat, lon = ll.split(",")
            return float(lat), float(lon)
    elif url.startswith("https://www.google.com/maps/dir/"):
        slash_splits = url.split("/")
        if len(slash_splits) > 6:
            lat, lon = slash_splits[6].split(",")
            return float(lat.strip()), float(lon.strip())

        for ll in get_query_param(url, "destination"):
            lat, lon = ll.split(",")
            return float(lat), float(lon)
    elif url.startswith("https://www.google.com/maps/place/"):
        lat, lon = url.split("/")[5].split(",")
        return float(lat.strip()), float(lon.strip())
    elif url.startswith("https://www.google.com/maps/search"):
        lat, lon = url.replace("https://www.google.com/maps/search/?api=1&query=", "").split(",")
        return float(lat.strip()), float(lon.strip())
    elif "daddr" in url:
        for daddr in get_query_param(url, "daddr"):
            daddr = daddr.split(",")
            if len(daddr) == 2:
                return float(daddr[0]), float(daddr[1])
    elif "maps.apple.com" in url:
        for q in get_query_param(url, "q"):
            coords = q.split(",")
            if len(coords) == 2:
                return float(coords[0]), float(coords[1])

    if "/maps.google.com/" in url:
        for ll in get_query_param(url, "ll"):
            lat, lon = ll.split(",")
            return float(lat), float(lon)

    return None, None
