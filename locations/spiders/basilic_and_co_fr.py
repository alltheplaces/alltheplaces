import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class BasilicAndCoFRSpider(SitemapSpider, StructuredDataSpider):
    name = "basilic_and_co"
    # "co" here is short for "& Co", not the ISO country code for Colombia.
    skip_auto_cc_spider_name_check = True
    item_attributes = {
        "brand": "Basilic & Co",
        "brand_wikidata": "Q130248490",
    }
    sitemap_urls = ["https://pizzerias.basilic-and-co.com/robots.txt"]
    sitemap_rules = [
        (r"/restaurant-pizza-terroir/", "parse_sd"),
    ]
    drop_attributes = {"image", "facebook"}
    wanted_types = ["Restaurant"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.RESTAURANT_PIZZA, item)
        item["branch"] = item.pop("name", "").removeprefix("Basilic & Co - pizzas de terroirs - ")

        data = response.css("display-schedule::attr(data-information)").get()
        if data:
            opening_hours_data = json.loads(data).get("hours")
            if isinstance(opening_hours_data, list):
                for day in opening_hours_data:
                    if not isinstance(day, dict):
                        continue

                    cur_day = day.get("day")
                    if cur_day is None:
                        continue

                    periods = day.get("periods")
                    if not isinstance(periods, list):
                        continue

                    for period in periods:
                        openTime = period.get("openTime")
                        closeTime = period.get("closeTime")
                        if period.get("isClosed"):
                            item["opening_hours"].set_closed(cur_day)
                        elif openTime is not None and closeTime is not None:
                            item["opening_hours"].add_range(
                                cur_day, openTime.replace(" ", ""), closeTime.replace(" ", "")
                            )

        yield item
