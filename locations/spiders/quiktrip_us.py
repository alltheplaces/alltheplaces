from typing import Any, Iterable

import chompjs
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class QuiktripUSSpider(SitemapSpider, StructuredDataSpider):
    name = "quiktrip_us"
    item_attributes = {"brand": "QuikTrip", "brand_wikidata": "Q7271953"}
    sitemap_urls = ["https://locations.quiktrip.com/robots.txt"]
    sitemap_rules = [(r"https://locations\.quiktrip\.com/\w\w/[-'\w]+/[-.'()\w]+$", "parse")]

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            if geo := chompjs.parse_js_object(block).get("credentialSubject", {}).get("geo"):
                item["lat"] = geo.get("latitude")
                item["lon"] = geo.get("longitude")

        services = response.xpath(
            '//h3[text()="LOCATION SERVICES"]/parent::div/following-sibling::ul[1]/li/text()'
        ).getall()
        fuel_types = response.xpath('//h3[text()="FUEL TYPES"]/parent::div/following-sibling::ul[1]/li/text()').getall()

        if fuel_types:
            apply_category(Categories.FUEL_STATION, item)
        else:
            apply_category(Categories.SHOP_CONVENIENCE, item)

        apply_yes_no(Extras.ATM, item, "ATM" in services)

        item["image"] = None
        yield item
