import json
from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import SocialMedia, set_social_media


class AlbertImmoSpider(Spider):
    name = "albert_immo"
    item_attributes = {"name": "Albert", "brand": "Albert"}
    start_urls = ["https://albert.immo/en/offices"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in DictParser.get_nested_key(
            json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()), "offices"
        ):
            if location["active"] is not True:
                continue

            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["housenumber"] = location["nr"]
            item["street"] = location["street"]
            item["image"] = urljoin("https://assets.albert.immo/", location["image"])
            item["website"] = urljoin("https://albert.immo/en/office/", location["slug"])
            item["extras"]["check_date"] = location["modified"].split("T", 1)[0]

            set_social_media(item, SocialMedia.FACEBOOK, location["social_facebook"])
            set_social_media(item, SocialMedia.INSTAGRAM, location["social_instagram"])
            apply_category(Categories.OFFICE_ESTATE_AGENT, item)

            yield item
