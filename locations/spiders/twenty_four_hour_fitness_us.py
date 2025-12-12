from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TwentyFourHourFitnessUSSpider(SitemapSpider, StructuredDataSpider):
    name = "twenty_four_hour_fitness_us"
    item_attributes = {"brand": "24 Hour Fitness", "brand_wikidata": "Q4631849"}
    sitemap_urls = ["https://www.24hourfitness.com/sitemap.xml"]
    sitemap_rules = [(r"/gyms/[^/]+/[^/]+", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if item["name"].endswith(" Super-Sport"):
            item["branch"] = item.pop("name").removeprefix("24 Hour Fitness ").removesuffix(" Super-Sport")
            item["name"] = "24 Hour Fitness Super Sport"
        elif item["name"].endswith(" Sport"):
            item["branch"] = item.pop("name").removeprefix("24 Hour Fitness ").removesuffix(" Sport")
            item["name"] = "24 Hour Fitness Sport"
        elif item["name"].endswith(" Active"):
            item["branch"] = item.pop("name").removeprefix("24 Hour Fitness ").removesuffix(" Active")
            item["name"] = "24 Hour Fitness"

        oh = OpeningHours()
        if response.xpath('//*[@id="gym-info-hours"]//li'):
            for day_time in response.xpath('//*[@id="gym-info-hours"]//li'):
                day_string = day_time.xpath('.//*[@class="ih-days"]/text()').get()
                time = day_time.xpath('.//*[@class="ih-hours"]/text()').get()
                if "-" in day_string:
                    start_day, end_day = day_string.split("-")
                else:
                    start_day = end_day = day_string.strip()
                open_time, close_time = time.split("-")
                oh.add_days_range(day_range(start_day, end_day), open_time.strip(), close_time.strip(), "%H:%M %p")
        elif time_string := response.xpath('//*[@id="gym-info-hours"]/p'):
            time_string = time_string.xpath(".//text()").get()
            if time_string == "OPEN 24/7":
                oh = "24/7"
        item["opening_hours"] = oh

        apply_category(Categories.GYM, item)

        yield item
