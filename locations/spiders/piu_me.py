from typing import Any

from scrapy.http import Response
from scrapy.spiders import CSVFeedSpider

from locations.items import Feature


class PiuMeSpider(CSVFeedSpider):
    name = "piu_me"
    item_attributes = {"brand": "PiùMe", "brand_wikidata": "Q113579745"}
    start_urls = ["https://connettore-piume.borasolab.it/storelocator/stores.csv"]
    skip_auto_cc_spider_name = True
    skip_auto_cc_domain = True

    def parse_row(self, response: Response, row: dict[str, str]) -> Any:
        item = Feature()
        item["branch"] = row["nome"].removeprefix("PiùMe").strip(" -")
        item["addr_full"] = row["indirizzo"]
        item["phone"] = row["telefono_negozio"]
        item["lon"] = row["Xcoord"]
        item["lat"] = row["Ycoord"]
        item["ref"] = row["uuid"]
        yield item
