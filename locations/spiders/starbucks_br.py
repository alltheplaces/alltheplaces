import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES


class StarbucksBRSpider(Spider):
    name = "starbucks_br"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES
    start_urls = ["https://starbucks.harmo.me/"]  # Locator found on https://starbucks.com.br/
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Using xpath we only get few POIs
        for ref, address, lat, lon, slug in re.findall(
            r"\"([0-9a-f]+)\"[,\s]+\"(.+?)\"[,\s]+.*?\"([-.\d]+)\"[,\s]+\"([-.\d]+)\"[,\s]+.*?\"(starbucks-[-\w]+)\"",
            response.xpath('//*[@id="__NUXT_DATA__"]/text()').get(""),
        ):
            item = Feature()
            item["ref"] = ref
            item["addr_full"] = address
            item["lat"] = lat
            item["lon"] = lon
            item["website"] = response.urljoin(slug)
            apply_category(Categories.COFFEE_SHOP, item)
            yield item
