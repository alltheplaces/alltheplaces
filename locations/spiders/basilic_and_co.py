from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories, apply_category
import json
from locations.hours import OpeningHours, DAYS_FR


class BasilicAndCoSpider(SitemapSpider, StructuredDataSpider):
    name = "basilic_and_co"
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
        apply_category(Categories.RESTAURANT, item)
        item["name"] = "Basilic & Co"
        
        try:
            oh = OpeningHours()
            opening_hours_data = json.loads(response.css("display-schedule::attr(data-information)").get())["hours"]
            for day in opening_hours_data:
                oh.add_ranges_from_string(day["formattedHour"].replace("h",":"), days=DAYS_FR)

            item["opening_hours"] = oh
            yield item
        except:
            yield item

