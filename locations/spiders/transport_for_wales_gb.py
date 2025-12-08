import json
import string

from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature


class TransportForWalesGBSpider(Spider):
    name = "transport_for_wales_gb"
    item_attributes = {"operator": "Transport for Wales", "operator_wikidata": "Q104878180"}
    start_urls = ["https://tfw.wales/api/stations/links/{}".format(letter) for letter in string.ascii_uppercase]

    def parse(self, response, **kwargs):
        for location in json.loads(response.json()):
            yield Request(
                url=location["link"],
                callback=self.parse_station,
                meta={"ref": location["crs_code"], "name": location["name"]},
            )

    def parse_station(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["extras"]["ref:crs"] = response.meta["ref"]
        item["name"] = response.meta["name"]
        item["website"] = response.url

        extract_google_position(item, response)

        apply_category(Categories.TRAIN_STATION, item)

        yield item
