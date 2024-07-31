from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import SocialMedia, set_social_media
from locations.pipelines.address_clean_up import merge_address_lines

SOCIAL_MEDIA_MAP = {
    "facebook": SocialMedia.FACEBOOK,
    "instagram": SocialMedia.INSTAGRAM,
    "pinterest": SocialMedia.PINTEREST,
    "snapchat": SocialMedia.SNAPCHAT,
    "tiktok": SocialMedia.TIKTOK,
    "tik tok ": SocialMedia.TIKTOK,
    "trip advisor": SocialMedia.TRIPADVISOR,
    "twitter": SocialMedia.TWITTER,
    "yelp": SocialMedia.YELP,
    "youtube": SocialMedia.YOUTUBE,
}

# stores could be obtained from https://api.mallmaverick.com/properties/{ref}/stores
# However coords is relative to a none north facing svg


class MallMaverickSpider(Spider):
    name = "mall_maverick"
    start_urls = ["https://api.mallmaverick.com/properties/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if location["status"] != "active" or location["property_manager_id"] == 3:
                continue
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            item["website"] = location["url"]

            for social_media in location["social_links"]:
                # Handle the case where the value in social_type is set to null
                social_media_lower = (social_media.get("social_type") or "").lower()

                # Some social media entries are just the social media website URLs and aren't useful
                if not (social_media.get("url") or "").startswith("http"):
                    continue

                if service := SOCIAL_MEDIA_MAP.get(social_media_lower):
                    set_social_media(item, service, social_media["url"])

            apply_category(Categories.SHOP_MALL, item)

            yield item
