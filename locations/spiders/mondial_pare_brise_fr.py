import json
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

OVERSEAS_COUNTRIES = {"971": "GP", "972": "MQ", "973": "GF", "974": "RE", "976": "YT"}


class MondialPareBriseFRSpider(SitemapSpider, StructuredDataSpider):
    name = "mondial_pare_brise_fr"
    item_attributes = {"brand": "Mondial Pare-Brise", "brand_wikidata": "Q118129474"}
    sitemap_urls = ["https://www.mondialparebrise.fr/robots.txt"]
    # Only the brand's own technical centres. The "point-relais-mondial-pare-brise-*"
    # pages are partner garages that host appointments without Mondial Pare-Brise staff.
    sitemap_rules = [(r"/trouver-mon-centre/mondial-pare-brise-[^/]+$", "parse_sd")]
    wanted_types = ["AutoRepair"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = response.xpath('//input[@id="centerCode"]/@value').get()
        item["branch"] = item.pop("name").removeprefix("Mondial Pare-Brise").strip()
        item["street_address"] = item.pop("street_address", "").strip(" ,") or None
        item.pop("addr_full", None)
        postcode = item.get("postcode") or ""
        if postcode == "97150":
            item["country"] = "MF"
        else:
            item["country"] = OVERSEAS_COUNTRIES.get(postcode[:3], "FR")
        if item.get("state") == "DROM 97":
            item.pop("state")
        # Many centres link the national page rather than their own.
        if (item.get("facebook") or "").rstrip("/") == "https://www.facebook.com/MondialPareBriseFrance":
            item.pop("facebook")

        # The JSON-LD coordinates are truncated and use a decimal comma; the map script has full precision.
        item["lat"] = response.xpath("//script/text()").re_first(r"latitude: '(-?[\d.]+)'")
        item["lon"] = response.xpath("//script/text()").re_first(r"longitude: '(-?[\d.]+)'")

        item["opening_hours"] = self.parse_opening_hours(response)

        apply_category(Categories.SHOP_CAR_REPAIR, item)
        apply_yes_no(Extras.VEHICLE_WINDSCREEN_REPLACEMENT_SERVICES, item, True)
        yield item

    @staticmethod
    def parse_opening_hours(response: TextResponse) -> OpeningHours | None:
        raw = response.xpath("//script/text()").re_first(r"const jsonData = JSON\.parse\(`(.+?)`\);")
        if not raw:
            return None
        oh = OpeningHours()
        for day in json.loads(raw)[0].get("openingTime") or []:
            for slot in (day.get("slot") or {}).values():
                if slot and slot.get("start") and slot.get("end"):
                    oh.add_range(DAYS_FR[day["name"].title()], slot["start"], slot["end"])
        return oh
