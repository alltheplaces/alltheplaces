from typing import Any

from chompjs import parse_js_object
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.items import SocialMedia, set_social_media
from locations.pipelines.address_clean_up import clean_address


class CarpetOneFloorAndHomeUSCASpider(SitemapSpider):
    name = "carpet_one_floor_and_home_us_ca"
    item_attributes = {"brand": "Carpet One Floor & Home", "brand_wikidata": "Q121335910"}
    sitemap_urls = [
        "https://www.carpetone.com/locations-sitemap.xml",
        "https://www.carpetone.ca/locations-sitemap.xml",
    ]
    # Scrape locations from state pages, reducing the number of requests
    sitemap_rules = [
        (r"^https:\/\/www\.carpetone\.com\/locations\/[^/]+$", "parse"),
        (r"^https:\/\/www\.carpetone\.ca\/locations\/[^/]+$", "parse"),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in parse_js_object(response.xpath('//script[contains(text(), "var locationlist")]/text()').get()):
            item = DictParser.parse(location)
            item["street_address"] = clean_address([location["address"].get("line1"), location["address"].get("line2")])
            item["phone"] = location["address"].get("phone")
            item["website"] = location.get("microSiteUrl")

            for social_media_account in location.get("socialMedia", []):
                if social_media_account.get("key") == "FacebookURL":
                    set_social_media(item, SocialMedia.FACEBOOK, social_media_account["value"])
                elif social_media_account.get("key") == "InstagramURL":
                    set_social_media(item, SocialMedia.INSTAGRAM, social_media_account["value"])

            yield item
