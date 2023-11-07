import re
from urllib.parse import parse_qs, urlsplit


def _get_possible_links(response):
    yield from response.xpath('//img[contains(@src, "maps/api/staticmap")]/@src').getall()
    yield from response.xpath('//iframe[contains(@src, "maps/embed")]/@src').getall()
    yield from response.xpath("//a[contains(@href, 'google')][contains(@href, 'maps')]/@href").getall()
    yield from response.xpath("//a[contains(@href, 'maps.apple.com')]/@href").getall()


def extract_google_position(item, response):
    for link in _get_possible_links(response):
        try:
            coords = url_to_coords(link)
            if coords != (None, None):
                item["lat"], item["lon"] = coords
                return
        except ValueError:
            return


def url_to_coords(url: str) -> (float, float):  # noqa: C901
    def get_query_param(link, query_param):
        parsed_link = urlsplit(link)
        queries = parse_qs(parsed_link.query)
        return queries.get(query_param, [])

    url = url.replace("google.co.uk", "google.com")

    if match := re.search(r"@(-?\d+.\d+),\s?(-?\d+.\d+),[\d.]+[zm]", url):
        return float(match.group(1)), float(match.group(2))

    if url.startswith("https://www.google.com/maps/embed?pb="):
        # https://andrewwhitby.com/2014/09/09/google-maps-new-embed-format/
        params = url[38:].split("!")
        maps_keys = {}
        for i in range(0, len(params)):
            if m := re.match(r"^(\d)d([-.\d]+)$", params[i]):
                maps_keys[m.group(1)] = m.group(2)
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
            if match := re.match(r"(-?\d+.\d+),\s?(-?\d+.\d+)", q):
                return float(match.group(1)), float(match.group(2))
    elif url.startswith("https://maps.googleapis.com/maps/api/staticmap"):
        for markers in get_query_param(url, "markers"):
            for val in markers.split("|"):
                if m := re.match(r"(-?\d+.\d+),(-?\d+.\d+)", val):
                    lat, lon = float(m.group(1)), float(m.group(2))
                    return lat, lon
    elif url.startswith("https://www.google.com/maps/dir/"):
        slash_splits = url.split("/")
        if len(slash_splits) > 6:
            lat, lon = slash_splits[6].split(",")
            if lat and lon:
                return float(lat.strip()), float(lon.strip())

        for ll in get_query_param(url, "destination"):
            if m := re.match(r"^(-?[.\d]+),(-?[.\d]+)$", ll):
                return float(m.group(1)), float(m.group(2))
    elif url.startswith("https://www.google.com/maps/place/"):
        slash_splits = url.split("/")
        if len(slash_splits) > 5:
            if m := re.match(r"(-?\d+.\d+),\s?(-?\d+.\d+)", slash_splits[5]):
                return float(m.group(1)), float(m.group(2))
    elif url.startswith("https://www.google.com/maps/search"):
        for query in get_query_param(url, "query"):
            if m := re.match(r"(-?\d+.\d+),(-?\d+.\d+)", query):
                return float(m.group(1)), float(m.group(2))
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

    for center in get_query_param(url, "center"):
        lat, lon = center.split(",")
        return float(lat), float(lon)

    # Fall back on 2 comma separated floats
    if match := re.search(r"(-?\d+\.\d+),\s?(-?\d+\.\d+)", url):
        return float(match.group(1)), float(match.group(2))

    return None, None
