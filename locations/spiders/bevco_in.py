import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response
from scrapy.selector import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature


class BevcoINSpider(Spider):
    name = "bevco_in"
    item_attributes = {"brand": "Bevco", "brand_wikidata": "Q6393413", "country": "IN", "state": "Kerala"}
    start_urls = ["https://bevco.in/shop-locations/"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for row in response.xpath("//tr[count(td)=7]"):
            yield from self.parse_row(row)

    def parse_row(self, row: Selector) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = row.xpath("normalize-space(./td[2])").get()
        item["branch"] = row.xpath("normalize-space(./td[3])").get()
        item["addr_full"] = re.sub(r"-\s*$", "", "".join(row.xpath("./td[5]//text()").getall())).strip()

        if m := re.search(r"query=\s*(-?\d{1,3}\.\d+),\s*(-?\d{1,3}\.\d+)", row.xpath("./td[5]//a/@href").get("")):
            item["lat"], item["lon"] = m.group(1), m.group(2)

        item["phone"] = row.xpath("./td[7]//a/@href").get("").removeprefix("tel:").strip()
        apply_category(Categories.SHOP_ALCOHOL, item)
        yield item
