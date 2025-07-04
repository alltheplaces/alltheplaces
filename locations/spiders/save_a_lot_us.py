from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import SocialMedia, set_social_media


class SaveALotUSSpider(SitemapSpider):
    name = "save_a_lot_us"
    item_attributes = {"brand": "Save-A-Lot", "brand_wikidata": "Q7427972"}
    sitemap_urls = ["https://savealot.com/sitemap.xml"]
    sitemap_rules = [(r"/stores/\d+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = chompjs.parse_js_object(
            response.xpath('//*[contains(text(),"window.__remixContext")]/text()').get()
        )["state"]["loaderData"]["routes/stores.$storeId._index"]["storeDetailsV2"]
        raw_data.update(raw_data.pop("location"))
        item = DictParser.parse(raw_data)
        item["branch"] = item.pop("name")
        item["website"] = response.url
        for link in raw_data["webLinks"]:
            if link["name"] == "Facebook":
                set_social_media(item, SocialMedia.FACEBOOK, link["url"])
                break
        for number in raw_data["phoneNumbers"]:
            if number["description"] == "Main":
                item["phone"] = number["value"]
                break

        item["opening_hours"] = self.parse_opening_hours(raw_data["hours"]["weekly"])

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if rule["daily"]["type"] == "CLOSED":
                oh.set_closed(rule["day"])
            elif rule["daily"]["type"] == "OPEN_24_HOURS":
                oh.add_range(rule["day"], "00:00", "24:00")
            else:
                oh.add_range(rule["day"], rule["daily"]["open"]["open"], rule["daily"]["open"]["close"], "%H:%M:%S")
        return oh
