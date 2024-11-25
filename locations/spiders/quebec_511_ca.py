from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class Quebec511CASpider(JSONBlobSpider):
    name = "quebec_511_ca"
    item_attributes = {"operator": "Transports Québec", "operator_wikidata": "Q3315417", "extras": Categories.SURVEILLANCE_CAMERA.value}
    allowed_domains = ["www.quebec511.info"]
    start_urls = ["https://www.quebec511.info/en/Carte/Element.ashx?action=Camera&xMin=-180&yMin=-90&xMax=180&yMax=90&lang=en"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = feature["info"]
        item["extras"]["contact:webcam"] = "https://www.quebec511.info/Carte/Fenetres/FenetreVideo.html?id=" + item["ref"]
        item["extras"]["camera:type"] = "fixed"
        yield item
