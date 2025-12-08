import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PoundbakeryGBSpider(SitemapSpider):
    name = "poundbakery_gb"
    item_attributes = {"brand": "Poundbakery", "brand_wikidata": "Q21061591"}
    sitemap_urls = ["https://www.poundbakery.co.uk/robots.txt"]
    sitemap_rules = [("/store/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["website"] = item["ref"] = response.url
        item["branch"] = (
            response.xpath('normalize-space(//h1[@class="store"]/text())').get().removeprefix("Poundbakery - ")
        )
        item["addr_full"] = merge_address_lines(response.xpath('//p[@class="address"]/text()').getall())
        item["phone"] = response.xpath('//p[@class="telephone"]/text()').get()
        item["image"] = response.urljoin(response.xpath('//img[@class="img-responsive img-store"]/@src').get())

        if m := re.search(r"LatLng\((-?\d+\.\d+), (-?\d+\.\d+)\);", response.text):
            item["lat"], item["lon"] = m.groups()

        yield item
