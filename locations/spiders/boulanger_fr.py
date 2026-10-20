import json
import random
from typing import Iterable

from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature, set_closed
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class BoulangerFRSpider(SitemapSpider, PlaywrightSpider):
    name = "boulanger_fr"
    item_attributes = {"brand": "Boulanger", "brand_wikidata": "Q2921695"}
    sitemap_urls = ["https://www.boulanger.com/sitemap_magasins.xml"]
    sitemap_rules = [(r"/magasins/(?!espaces/|actualites/)[^/]+/[^/]+/[^/]+/[^/]+$", "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT} | DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        raw = response.css("#js-map-config-dir-map::text").get()
        try:
            entities = json.loads(raw).get("entities") if raw else None
        except json.JSONDecodeError:
            entities = None
        if not entities:
            if response.request is not None:
                if retry := get_retry_request(
                    response.request,
                    spider=self,
                    reason="no map-config JSON found",
                    priority_adjust=random.randint(-20, -1),
                ):
                    yield retry
            return
        profile = entities[0]["profile"]

        item = DictParser.parse(profile)
        item["ref"] = profile["meta"]["id"]
        item["website"] = response.url  # profile's own websiteUrl can point at a stale domain
        item.pop("phone")  # same national hotline (09 69 32 32 23) on every store, not per-branch
        item["state"] = None  # a French département name, not a real addr:state value
        if item["name"].startswith("Connexion Partenaire Boulanger "):
            item["branch"] = item.pop("name").removeprefix("Connexion Partenaire Boulanger ")
            item["name"] = "Connexion Partenaire Boulanger"
        else:
            item["branch"] = " ".join(item.pop("name", "").removeprefix("Boulanger").strip(" -").split())

        address = profile.get("address") or {}
        item["street_address"] = merge_address_lines([address.get("line1"), address.get("line2"), address.get("line3")])

        item["opening_hours"] = self.parse_hours(profile.get("hours", {}).get("normalHours", []))

        apply_yes_no(PaymentMethods.GOOGLE_PAY, item, "Google Pay" in profile["paymentOptions"])
        apply_yes_no(PaymentMethods.CASH, item, "Cash" in profile["paymentOptions"])
        apply_yes_no(PaymentMethods.MASTER_CARD, item, "MasterCard" in profile["paymentOptions"])
        apply_yes_no(PaymentMethods.VISA, item, "Visa" in profile["paymentOptions"])

        apply_category(Categories.SHOP_ELECTRONICS, item)

        if profile.get("closed") is True:
            set_closed(item)

        yield item

    @staticmethod
    def parse_hours(normal_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for day in normal_hours:
            if day.get("isClosed"):
                oh.set_closed(day["day"])
                continue
            for interval in day.get("intervals", []):
                start = f"{interval['start'] // 100:02d}:{interval['start'] % 100:02d}"
                end = f"{interval['end'] // 100:02d}:{interval['end'] % 100:02d}"
                oh.add_range(day["day"], start, end)
        return oh
