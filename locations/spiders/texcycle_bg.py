from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class TexcycleBGSpider(Spider):
    name = "texcycle_bg"
    item_attributes = {"operator": "TexCycle", "operator_wikidata": "Q85614408"}
    allowed_domains = ["www.texcycle.bg"]
    start_urls = ["https://texcycle.bg/bin-locations-list/"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for row in response.xpath('//div[@class="post-content"]//tbody//tr'):
            name = row.xpath("./td[2]/text()").get()
            coords = row.xpath("./td[3]/text()").get().split(",")

            item = Feature(name=name, lat=coords[0], lon=coords[1])
            apply_category(Categories.RECYCLING, item)
            yield item
