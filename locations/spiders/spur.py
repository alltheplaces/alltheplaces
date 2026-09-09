from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.rocomamas import RocomamasSpider


class SpurSpider(RocomamasSpider):
    name = "spur"
    brands = {"SPUR": {"brand": "Spur", "brand_wikidata": "Q7581546"}}

    async def start(self) -> AsyncIterator[Request]:
        yield JsonRequest(
            url=self.start_urls[0],
            data={
                "url": "restaurants?brandKey={}&tradingStatus=Open&filterHidden=true&expand=channels".format(
                    ",".join(self.brands.keys())
                ),
                "method": "GET",
            },
        )

    def parse_store(self, response: Response) -> Iterable[Feature]:
        for item in super().parse_store(response):
            # Names such as "Buffalo Hills Spur Steak Ranch" leave a double space behind.
            item["branch"] = " ".join(item["branch"].split())
            item.pop("website", None)
            apply_category(Categories.RESTAURANT, item)
            yield item
