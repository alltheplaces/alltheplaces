from urllib.parse import parse_qs, unquote, urlsplit

from scrapy import Selector
from scrapy.http import Response

from locations.items import Feature


def _get_possible_links(response: Response | Selector):
    yield from response.xpath(".//a[contains(@href, 'mapy.cz')]/@href").getall()


def extract_mapy_cz_position(item: Feature, response: Response | Selector):
    for link in _get_possible_links(response):
        try:
            coords = url_to_coords(link)
            if coords != (None, None):
                item["lat"], item["lon"] = coords
                return
        except ValueError:
            return


def url_to_coords(url: str) -> (float, float):
    def get_query_param(link, query_param):
        parsed_link = urlsplit(link)
        queries = parse_qs(parsed_link.query)
        return queries.get(query_param, [])

    url = unquote(url)

    # https://mapy.cz/zakladni?source=base&id=1892282&x=14.4044792&y=50.0921223&z=17
    for x in get_query_param(url, "x"):
        for y in get_query_param(url, "y"):
            return float(y), float(x)

    # https://mapy.cz/zakladni?q=50.1222139N,14.4138156E
    for q in get_query_param(url, "q"):
        lat, lon = None, None
        for coord in q.split(","):
            if coord.endswith("N") or coord.endswith("S"):
                lat = coord.removesuffix("N").removesuffix("S")
            if coord.endswith("E") or coord.endswith("W"):
                lon = coord.removesuffix("E").removesuffix("W")
        if lat and lon:
            return float(lat), float(lon)

    # https://developer.mapy.cz/en/further-uses-of-mapycz/mapy-cz-url/
    for center in get_query_param(url, "center"):
        lon, lat = center.split(",")
        return float(lat), float(lon)

    if url.startswith("https://mapy.cz/fnc/v1/route"):
        starts = get_query_param(url, "start")
        ends = get_query_param(url, "end")
        # extract either start or end, but not both
        if len(starts) == 0 and len(ends) == 1:
            lon, lat = ends[0].split(",")
            return float(lat), float(lon)
        if len(starts) == 1 and len(ends) == 0:
            lon, lat = starts[0].split(",")
            return float(lat), float(lon)

    return None, None
