import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider

REGULAR_HOURS_TITLES = {
    "Weekdays",
    "Weekends",
    "Monday–Friday",
    "Monday–Thursday",
    "Friday",
    "Fridays",
    "Saturday",
    "Sunday",
    "Saturday–Sunday",
}


class NuffieldHealthGBSpider(SitemapSpider, StructuredDataSpider):
    name = "nuffield_health_gb"
    item_attributes = {"brand_wikidata": "Q7068711"}
    sitemap_urls = ["https://www.nuffieldhealth.com/robots.txt"]
    sitemap_follow = ["gyms"]
    sitemap_rules = [(r"/gyms/([^/]+)$", "parse")]
    wanted_types = ["ExerciseGym"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if response.url == "https://www.nuffieldhealth.com/gyms/247":
            return

        if coords := response.xpath('//div[@class="location__map"]/@data-markers').get():
            coords = json.loads(coords)[0]
            item["lat"] = coords["lat"]
            item["lon"] = coords["lon"]
        item["phone"] = response.xpath('//span[@class="location__telephone"]/span[@itemprop="telephone"]/text()').get()

        item["opening_hours"] = OpeningHours()
        for title in response.xpath(
            '(//div[contains(@class, "location__opening-times")])[1]//span[@class="location__opening-times__title"]'
        ):
            day = title.xpath("normalize-space()").get()
            if day in REGULAR_HOURS_TITLES:
                hours = title.xpath("normalize-space(following-sibling::text()[1])").get()
                item["opening_hours"].add_ranges_from_string(day + hours)

        apply_category(Categories.GYM, item)
        yield item
