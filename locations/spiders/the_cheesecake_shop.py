import json
from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature, SocialMedia, set_social_media
from locations.react_server_components import parse_rsc
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class TheCheesecakeShopSpider(Spider):
    name = "the_cheesecake_shop"
    item_attributes = {"brand": "The Cheesecake Shop", "brand_wikidata": "Q117717103"}
    start_urls = [
        "https://www.cheesecake.com.au/find-bakery/",
        "https://www.thecheesecakeshop.co.nz/store-locations",
    ]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        country = "AU" if "cheesecake.com.au" in response.url else "NZ"
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(s for _, s in (chompjs.parse_js_object(script) for script in scripts) if isinstance(s, str))
        for _, value in parse_rsc(rsc.encode()):
            if not (isinstance(value, str) and '"storeSysId"' in value):
                continue
            location = json.loads(value)
            item = DictParser.parse(location)
            # The two countries' sites use overlapping storeSysId ranges.
            item["ref"] = "{}-{}".format(country, location["storeSysId"])
            item["branch"] = item.pop("name")
            item["website"] = response.urljoin("/store-locations/{}".format(location["storeIdentifier"]))

            if facebook := location.get("storeFacebook"):
                set_social_media(item, SocialMedia.FACEBOOK, facebook)
            if instagram := location.get("storeInstagram"):
                set_social_media(item, SocialMedia.INSTAGRAM, instagram)

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                " ".join(
                    "{}: {}".format(day, location.get("store{}Open".format(day.title())) or "")
                    for day in ["mon", "tue", "wed", "thur", "fri", "sat", "sun"]
                )
            )

            apply_category(Categories.SHOP_BAKERY, item)
            yield item
