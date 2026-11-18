import re

from scrapy.http import JsonRequest, Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MobalpaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "mobalpa_fr"
    item_attributes = {"brand": "Mobalpa", "brand_wikidata": "Q3317571", "name": "Mobalpa"}
    allowed_domains = ["www.mobalpa.fr", "api.mobalpa.fr"]
    sitemap_urls = ["https://www.mobalpa.fr/sitemap.xml"]
    sitemap_rules = [(r"/magasin/[^/]+$", "parse_sd")]
    wanted_types = ["Store"]
    search_for_twitter = False
    search_for_facebook = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["ref"] = response.url.split("/")[-1]
        item["branch"] = item.pop("name").removeprefix("Mobalpa ").removeprefix("MOBALPA ")
        item.pop("image", None)
        # Postcodes are numbers in the structured data, so leading zeros are lost
        item["postcode"] = str(ld_data["address"]["postalCode"]).zfill(5)
        item["opening_hours"] = self.parse_hours(ld_data.get("openingHours", ""))
        # NSI only matches mainland France, so overseas stores need the category set here
        apply_category(Categories.SHOP_KITCHEN, item)
        # The coordinates are only in the store API
        yield JsonRequest(
            f"https://api.mobalpa.fr/fournier/api/v1/slug?slug=/magasin/{item['ref']}",
            callback=self.parse_coordinates,
            cb_kwargs={"item": item},
        )

    def parse_coordinates(self, response: Response, item: Feature):
        coordinates = response.json().get("coordinates") or {}
        item["lat"] = coordinates.get("lat")
        item["lon"] = coordinates.get("lng")
        yield item

    @staticmethod
    def parse_hours(hours: str) -> OpeningHours:
        # e.g. "[Mo Fermé-Fermé],[Tu,We,Th,Fr,Sa 10:00-12:00,14:00-19:00]"
        oh = OpeningHours()
        for days, times in re.findall(r"\[([A-Za-z,]+) ([^\]]+)\]", hours):
            for day in days.split(","):
                if "Fermé" in times:
                    oh.set_closed(day)
                    continue
                for time_range in times.split(","):
                    open_time, close_time = time_range.strip().split("-")
                    oh.add_range(day, open_time, close_time)
        return oh
