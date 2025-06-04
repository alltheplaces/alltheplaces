import chompjs
from scrapy.http import Response

from locations.json_blob_spider import JSONBlobSpider


class DinoPLSpider(JSONBlobSpider):
    name = "dino_pl"
    item_attributes = {"brand": "Dino", "brand_wikidata": "Q11694239"}
    allowed_domains = ["marketdino.pl"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://marketdino.pl/map"]
    no_refs = True

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "mapData")]/text()').re_first(r"data[:\s]+(\[{.+}\]),")
        )[0]["mapData"]["features"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))
