from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FeuVertFRSpider(SitemapSpider, StructuredDataSpider):
    name = "feu_vert_fr"
    item_attributes = {"brand": "Feu Vert", "brand_wikidata": "Q3070922"}
    allowed_domains = ["www.feuvert.fr"]
    sitemap_urls = ["https://www.feuvert.fr/sitemap/centres-auto.xml"]
    sitemap_rules = [(r"/centres-auto/[^/]+/[^/]+/\d+\.html$", "parse_sd")]
    wanted_types = ["AutoRepair"]
    # Réunion/Martinique/Guadeloupe stores need their own country code (RE/MQ/GP); let the
    # reverse geocoder decide per store instead of assuming every item is "FR".
    skip_auto_cc_spider_name = True
    skip_auto_cc_domain = True
    # robots.txt disallows nothing we need here, and skipping it avoids an extra request.
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def _parse_sitemap(self, response):
        # Store pages need browserHtml: Zyte returns an empty httpResponseHeaders list for
        # this site, which leaves automap's httpResponseBody response without a .selector.
        for request in super()._parse_sitemap(response):
            request.meta["zyte_api"] = {
                "browserHtml": True,
                "geolocation": "FR",
                "javascript": True,
            }
            yield request

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        # Coordinates are top-level "latitude"/"longitude", not nested under "geo" like
        # LinkedDataParser expects.
        if lat := ld_data.get("latitude"):
            item["lat"] = lat
        if lon := ld_data.get("longitude"):
            item["lon"] = lon

        item.pop("image", None)  # Same generic illustration on every store, not a real photo

        # addressCountry is "fr" even for overseas-territory stores; drop it so
        # CountryCodeCleanUpPipeline's reverse geocoder assigns RE/MQ/GP where appropriate.
        item.pop("country", None)

        # Hours are under "hoursAvailable", not "openingHoursSpecification"; each entry's
        # dayOfWeek may be a single object or a list of them.
        if hours := ld_data.get("hoursAvailable"):
            item["opening_hours"] = OpeningHours()
            for rule in hours if isinstance(hours, list) else [hours]:
                days = rule.get("dayOfWeek")
                days = days if isinstance(days, list) else [days]
                for day in days:
                    day = day.get("name") if isinstance(day, dict) else day
                    item["opening_hours"].add_range(day, rule.get("opens"), rule.get("closes"))

        apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item
