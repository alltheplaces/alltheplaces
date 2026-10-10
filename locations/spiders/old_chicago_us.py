from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature


class OldChicagoUSSpider(SitemapSpider):
    name = "old_chicago_us"
    item_attributes = {"brand": "Old Chicago", "brand_wikidata": "Q64411347"}
    sitemap_urls = ["https://oldchicago.com/sitemap_index.xml"]
    sitemap_rules = [(r"https://oldchicago.com/locations/us/[^/]+/[^/]+/[^/]+/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = response.xpath("//h2/text()").get()
        addr_lines = response.xpath('//*[@class="location-address"]/a//text()').getall()
        item["street_address"] = addr_lines[0].strip() if addr_lines else None
        if len(addr_lines) > 1:
            city, _, rest = addr_lines[1].strip().partition(",")
            state, _, postcode = rest.strip().partition(",")
            item["city"] = city.strip()
            item["state"] = state.strip()
            item["postcode"] = postcode.strip()
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["ref"] = item["website"] = response.url
        yield item
