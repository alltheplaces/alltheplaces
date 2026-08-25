from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class RaSushiUSSpider(SitemapSpider):
    name = "ra_sushi_us"
    item_attributes = {"brand": "RA Sushi", "brand_wikidata": "Q117400401"}
    sitemap_urls = ["https://rasushi.com/locations-sitemap.xml"]
    sitemap_rules = [(r"/locations/.+", "parse_store")]

    def parse_store(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.url.split("/")[-2]
        item["branch"] = response.xpath("//h1//text()").get("").strip()
        item["addr_full"] = (
            response.xpath('//div[contains(@class, "contact-info__address")]/p/text()').get()
            or response.xpath('//p[strong[text()="Address"]]/following-sibling::p[1]/text()').get()
        )
        item["phone"] = response.xpath('//a[starts-with(@href, "tel:")]/text()').get()
        item["website"] = response.url
        if script := response.xpath('//script[contains(text(), "mapConfig = ")]/text()').get():
            map_config = chompjs.parse_js_object(script.split("mapConfig = ", 1)[1])
            item["lat"] = map_config.get("latitude")
            item["lon"] = map_config.get("longitude")
        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('(//div[@class="operating-times"])[1]//li/text()').getall():
            item["opening_hours"].add_ranges_from_string(rule.replace("Midnight", "11:59PM"))
        apply_category(Categories.RESTAURANT, item)
        yield item
