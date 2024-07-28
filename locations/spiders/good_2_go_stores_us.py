import json
from urllib.parse import unquote

from scrapy import Spider

from locations.items import Feature


class Good2GoStoresUSSpider(Spider):
    name = "good_2_go_stores_us"
    item_attributes = {"brand": "Good 2 Go", "brand_wikidata": "Q109826132"}
    start_urls = ["https://good2gostores.com/locations/"]
    no_refs = True

    def parse(self, response, **kwargs):
        for location in json.loads(unquote(response.xpath("//@data-elfsight-google-maps-options").get()))["markers"]:
            item = Feature()
            item["lat"], item["lon"] = location["coordinates"].split(", ")
            item["name"] = location["infoTitle"]
            item["addr_full"] = location["infoAddress"]
            item["phone"] = location["infoPhone"]
            item["email"] = location["infoEmail"]

            yield item
