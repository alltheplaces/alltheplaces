import json
import re
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class BpetTRSpider(Spider):
    name = "bpet_tr"
    item_attributes = {"brand": "Bpet", "brand_wikidata": "Q25475602"}
    start_urls = ["https://www.bpet.com.tr/en/bayi-haritasi"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for match in re.finditer(r'\{"photo_id":.+?\}', response.text):
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                continue
            yield Request(
                url=response.urljoin(data["owner_url"]),
                callback=self.parse_station,
                meta={
                    "ref": data["photo_id"],
                    "lat": data["latitude"],
                    "lon": data["longitude"],
                },
            )

    def parse_station(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.meta["ref"]
        item["lat"] = response.meta["lat"]
        item["lon"] = response.meta["lon"]
        item["website"] = response.url
        item["name"] = response.xpath("//main/h3/text()").get()
        item["addr_full"] = response.xpath("//main/h4/text()").get("").strip()
        apply_category(Categories.FUEL_STATION, item)
        yield item
