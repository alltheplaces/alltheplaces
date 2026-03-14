from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours

DQ_GRILL_CHILL = {"name": "DQ Grill & Chill", "brand": "DQ Grill & Chill", "brand_wikidata": "Q1141226"}
DQ = {"name": "Dairy Queen", "brand": "Dairy Queen", "brand_wikidata": "Q1141226"}


class DairyQueenSpider(Spider):
    name = "dairy_queen"
    allowed_domains = ["prod-dairyqueen.dotcmscloud.com"]
    start_urls = ["https://prod-dairyqueen.dotcmscloud.com/api/es/search"]
    item_attributes = {"nsi_id": "N/A"}
    WEBSITE_BY_COUNTRY = {
        "US": "https://www.dairyqueen.com/en-us/",
        "CA": "https://www.dairyqueen.com/en-ca/",
        "MX": "https://dairyqueen.com.mx/es-mx/",
        # working URL not found for below countries:
        "BS": None,
        "QA": None,
    }

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

            concept_type = location.get("conceptType")

            if not concept_type:
                self.logger.error("Store concept type not available")
            else:
                if concept_type in ["Food and Treat", "Treat & Food"]:
                    item.update(DQ_GRILL_CHILL)
                    apply_category(Categories.FAST_FOOD, item)
                    item["extras"]["cuisine"] = "ice_cream;burger"
                elif concept_type == "Treat Only":
                    item.update(DQ)
                    apply_category(Categories.FAST_FOOD, item)
                    item["extras"]["cuisine"] = "ice_cream"
                else:
                    self.logger.error("Unexpected type: {}".format(concept_type))

            item["street_address"] = location.get("address3")

            if website := self.WEBSITE_BY_COUNTRY.get(item["country"]):
                item["website"] = urljoin(website, location.get("urlTitle").lstrip("/"))
            else:
                item["website"] = None

            item["opening_hours"] = self.parse_opening_hours(location.get("storeHours"))
            yield item

    def parse_opening_hours(self, rules: str) -> OpeningHours | None:
        if not rules:
            return None
        opening_hours = OpeningHours()
        for rule in rules.split(","):
            day, hours = rule.split(":", 1)
            opening_hours.add_range(DAYS[int(day) - 1], *hours.split("-"))
        return opening_hours
