import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class BasilicAndCompanyFRSpider(SitemapSpider, StructuredDataSpider):
    name = "basilic_and_company_fr"
    item_attributes = {"brand": "Basilic & Co", "brand_wikidata": "Q130248490"}
    sitemap_urls = ["https://pizzerias.basilic-and-co.com/robots.txt"]
    sitemap_rules = [(r"/fr/restaurant-pizza-terroir/([^/]+)/$", "parse_sd")]
    drop_attributes = {"image", "facebook"}
    wanted_types = ["Restaurant"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name", "").removeprefix("Basilic & Co - pizzas de terroirs - ")

        if data := response.css("display-schedule::attr(data-information)").get():
            try:
                item["opening_hours"] = self.parse_opening_hours(data)
            except Exception:
                pass

        apply_category(Categories.RESTAURANT, item)

        yield item

    def parse_opening_hours(self, data: str) -> OpeningHours:
        oh = OpeningHours()
        for rule in json.loads(data)["hours"]:
            for period in rule["periods"]:
                if period.get("isClosed"):
                    oh.set_closed(rule["day"])
                else:
                    oh.add_range(rule["day"], period["openTime"].replace(" ", ""), period["closeTime"].replace(" ", ""))
        return oh
