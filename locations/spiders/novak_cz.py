import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class NovakCZSpider(Spider):
    name = "novak_cz"
    item_attributes = {"brand_wikidata": "Q58490605"}
    start_urls = ["https://masonovak.cz/o-nas/kde-nas-najdete"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath('//script[@class="map-data"]/text()').get())["markers"]:
            item = Feature()
            item["lat"] = location["lat"]
            item["lon"] = location["lon"]
            item["ref"] = item["website"] = response.urljoin(location["url"])
            apply_category(Categories.SHOP_BUTCHER, item)
            yield item
