import scrapy
from scrapy import Spider

from locations.hours import DAYS_BG, OpeningHours, sanitise_day
from locations.items import Feature


class YettelBGSpider(Spider):
    name = "yettel_bg"
    item_attributes = {
        "brand": "Yettel",
        "brand_wikidata": "Q14915070",
        "country": "BG",
    }
    start_urls = ["https://www.yettel.bg/store-locator/json"]
    no_refs = True
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        json_data = response.json()
        for store in json_data["features"]:
            item = Feature()

            item["lat"] = store["geometry"]["coordinates"][1]
            item["lon"] = store["geometry"]["coordinates"][0]

            html_description = store["properties"]["description"]
            description_selector = scrapy.Selector(text=html_description)
            item["street_address"] = description_selector.xpath('//div[@class="thoroughfare"]/text()').get()

            item["opening_hours"] = OpeningHours()
            hours_by_day = description_selector.xpath('//span[@class="oh-display"]')

            for day_hours in hours_by_day:
                day = sanitise_day(
                    day_hours.xpath('.//span[@class="oh-display-label"]/text()')
                    .get()
                    .replace(":", "")
                    .replace(".", "")
                    .strip(),
                    DAYS_BG,
                )
                hours = day_hours.xpath('.//div[contains(@class, "oh-display-times")]/text()').get().strip()
                if hours == "затворено":
                    continue
                open_time, close_time = hours.split("-")
                item["opening_hours"].add_range(day, open_time, close_time)

            yield item
