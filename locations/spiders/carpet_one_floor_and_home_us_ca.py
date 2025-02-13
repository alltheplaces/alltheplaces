from typing import Any

from chompjs import parse_js_object
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class CarpetOneFloorAndHomeUSCASpider(SitemapSpider):
    name = "carpet_one_floor_and_home_us_ca"
    item_attributes = {
        "brand": "Carpet One Floor & Home",
        "brand_wikidata": "Q121335910",
        "extras": Categories.SHOP_FLOORING.value,
    }
    sitemap_urls = [
        "https://www.carpetone.com/locations-sitemap.xml",
        "https://www.carpetone.ca/locations-sitemap.xml",
    ]
    sitemap_rules = [
        (r"^https:\/\/www\.carpetone\.com\/locations\/[^/]+/[^/]+$", "parse"),
        (r"^https:\/\/www\.carpetone\.ca\/locations\/[^/]+/[^/]+$", "parse"),
    ]
    # Attempt crawling with a high delay to try and avoid receiving
    # truncated binary responses (non-HTTP). Possible rate limiting
    # mechanism to frustrate bots?
    download_delay = 10

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in parse_js_object(response.xpath('//script[contains(text(), "var locationlist")]/text()').get()):
            item = DictParser.parse(location)
            item["street_address"] = clean_address([location["address"].get("line1"), location["address"].get("line2")])
            item["phone"] = location["address"].get("phone")
            item["website"] = location.get("microSiteUrl")

            for social_media_account in location.get("socialMedia", []):
                if social_media_account.get("key") == "FacebookURL":
                    item["facebook"] = social_media_account["value"]
                elif social_media_account.get("key") == "InstagramURL":
                    if not isinstance(item.get("extras"), dict):
                        item["extras"] = {}
                    item["extras"]["contact:instagram"] = social_media_account["value"]

            yield item
