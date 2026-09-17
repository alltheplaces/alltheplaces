import re

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The map page embeds one `google.maps.Marker` declaration per charging
# station directly in inline JavaScript, rather than exposing a JSON/API feed.
MARKER_PATTERN = re.compile(
    r"var marker(\d+) = new google\.maps\.Marker\(\{\s*"
    r"position: \{ lat: ([\d.-]+), lng: ([\d.-]+)\},\s*"
    r"map: map,\s*"
    r"title: '((?:[^'\\]|\\.)*)'"
)


class ZunderSpider(Spider):
    name = "zunder"
    item_attributes = {"operator": "Zunder", "operator_wikidata": "Q126870872"}
    start_urls = ["https://www.zunder.com/mapa-de-ubicaciones/"]

    def parse(self, response: Response):
        for ref, lat, lon, title in MARKER_PATTERN.findall(response.text):
            item = Feature()
            item["ref"] = ref
            item["lat"] = lat
            item["lon"] = lon
            item["branch"] = title.replace("\\'", "'")
            apply_category(Categories.CHARGING_STATION, item)
            yield item
