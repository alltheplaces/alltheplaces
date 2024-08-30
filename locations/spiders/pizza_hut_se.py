import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_SE, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PizzaHutSESpider(SitemapSpider):
    name = "pizza_hut_se"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    sitemap_urls = ["https://www.pizzahut.se/tools/googlesitemap"]
    sitemap_rules = [(r"/pizza/", "parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = item["website"] = response.url
        store_details = response.xpath('//*[@class="restaurants--list_item"]')
        item["name"] = store_details.xpath('//a[contains(text(),"Pizza Hut")]/text()').get()
        address = merge_address_lines(store_details.xpath('//*[@class="text-left"]/text()').getall())
        item["street_address"] = address.split("Tel:")[0].strip(", ")
        item["email"] = store_details.xpath('//a[contains(@href, "mailto")]/text()').get()
        item["phone"] = store_details.xpath('//a[contains(@href, "tel")]/text()').get()
        item["opening_hours"] = OpeningHours()
        for start_day, end_day, open_time, close_time in re.findall(
            r"(?:(\w+)[-\s]+)?(\w+)\s+(\d+[:.]\d+)\s*-\s*(\d+[:.]\d+)", store_details.get()
        ):
            start_day, end_day = [day.replace("Tor", "Tors") + "dag" if day else None for day in [start_day, end_day]]
            end_day = sanitise_day(end_day, DAYS_SE)
            start_day = sanitise_day(start_day, DAYS_SE) or end_day
            if start_day:
                item["opening_hours"].add_days_range(
                    day_range(start_day, end_day), open_time.replace(".", ":"), close_time.replace(".", ":")
                )
        apply_category(Categories.RESTAURANT, item)
        yield item
