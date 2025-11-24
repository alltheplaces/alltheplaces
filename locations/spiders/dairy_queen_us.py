from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

DQ_GRILL_CHILL = {"name": "DQ Grill & Chill", "brand": "DQ Grill & Chill", "brand_wikidata": "Q1141226"}
DQ = {"name": "Dairy Queen", "brand": "Dairy Queen", "brand_wikidata": "Q1141226"}


class DairyQueenUSSpider(Spider):
    name = "dairy_queen_us"
    allowed_domains = ["prod-dairyqueen.dotcmscloud.com"]
    start_urls = ["https://prod-dairyqueen.dotcmscloud.com/api/es/search"]
    item_attributes = {"nsi_id": "N/A"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=self.start_urls[0],
            method="POST",
            headers={
                "Referer": "https://www.dairyqueen.com/",
            },
            data={"size": 10000, "query": {"bool": {"must": [{"term": {"contenttype": "locationDetail"}}]}}},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["contentlets"]:
            item = DictParser.parse(location)
            item["lat"], item["lon"] = location.get("latlong", ",").split(",", 2)

            if location["conceptType"] == "Food and Treat":
                item.update(DQ_GRILL_CHILL)
                apply_category(Categories.FAST_FOOD, item)
                item["extras"]["cuisine"] = "ice_cream;burger"
            elif location["conceptType"] == "Treat Only":
                item.update(DQ)
                apply_category(Categories.FAST_FOOD, item)
                item["extras"]["cuisine"] = "ice_cream"
            else:
                self.logger.error("Unexpected type: {}".format(location["conceptType"]))

            item["street_address"] = location.get("address3")
            item["website"] = urljoin("https://www.dairyqueen.com", location.get("urlTitle"))

            yield item
