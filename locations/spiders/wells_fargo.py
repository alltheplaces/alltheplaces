import re
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class WellsFargoSpider(scrapy.Spider):
    name = "wells_fargo"
    item_attributes = {
        "brand": "Wells Fargo",
        "brand_wikidata": "Q744149",
        "country": "US",
    }
    allowed_domains = ["www.wellsfargo.com"]
    # This sitemap is invalid, so parse straight from response.text here
    start_urls = ["https://www.wellsfargo.com/locator/sitemap2"]

    def parse(self, response):
        for link in response.text.split("\n")[:-1]:
            yield scrapy.Request(link, callback=self.parse_poi)

    def parse_poi(self, response, **kwargs):
        item = Feature()
        item["website"] = response.url
        item["ref"] = response.url.split("/")[-2]
        item["addr_full"] = response.xpath('.//div[@itemprop="addressRegion"]/text()').get()
        item["city"] = response.xpath('.//span[@itemprop="addressLocality"]/text()').get()
        item["state"] = response.xpath('.//abbr[@itemprop="addressRegion"]/text()').get()
        item["postcode"] = response.xpath('.//span[@itemprop="postalCode"]/text()').get()
        item["phone"] = response.xpath('.//div[@itemprop="telephone"]/text()').get()
        self.parse_category(item, response)
        self.parse_coords(item, response)
        self.parse_hours(item, response)
        yield item

    def parse_category(self, item, response):
        if category := response.xpath('//div[not(@itemprop) and @class="fn heading"]/text()').get(default="").strip():
            if category == "Bank + ATM":
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, response)
            elif category == "Bank Only":
                apply_category(Categories.BANK, item)
            elif category == "ATM":
                apply_category(Categories.ATM, item)
            else:
                apply_category(Categories.BANK, item)
        else:
            apply_category(Categories.BANK, item)

    def parse_coords(self, item, response):
        if geo_link := response.xpath('//img[contains(@alt, "Bank location centered on map")]/@src').get():
            coords = Path(urlparse(geo_link).path).parts[-2]
            lat, lon = coords.split(",")
            item["lat"] = lat
            item["lon"] = lon

    def parse_hours(self, item, response):
        if has_category(item, Categories.BANK):
            if hours := response.xpath(
                '//h3[contains(text(), "Lobby Hours")]/following-sibling::ul[1]/li[@itemprop="openingHours"]/text()'
            ).get():
                item["opening_hours"] = self.store_hours(hours)
        elif has_category(item, Categories.ATM):
            # TODO: parse ATM hours
            pass

    def store_hours(self, hours_range):
        # TODO: use OpeningHours class
        day_range, time_range = hours_range.split(" ", 1)
        day_range = (
            day_range.replace("Mon", "Mo")
            .replace("Tue", "Tu")
            .replace("Thu", "Th")
            .replace("Fri", "Fr")
            .replace("Sat", "Sa")
            .replace("Sun", "Su")
        )

        if time_range == "closed":
            pass

        match = re.search(r"^(\d{2}):(\d{2}) ([AP])M-(\d{2}):(\d{2}) ([AP])M$", time_range)
        if not match:
            self.logger.warning("Could not parse time_range for %s", time_range)
            self.crawler.stats.inc_value("atp/wellsfargo/hours/failed")

        (f_hr, f_min, f_ampm, t_hr, t_min, t_ampm) = match.groups()

        if f_ampm == "P":
            f_hr = int(f_hr) + 12
        if t_ampm == "P":
            t_hr = int(t_hr) + 12

        time_range = "{:02d}:{:02d}-{:02d}:{:02d}".format(
            int(f_hr),
            int(f_min),
            int(t_hr),
            int(t_min),
        )

        return "{} {}".format(day_range, time_range)


def has_category(item: Feature, category: Enum):
    if isinstance(category, Enum):
        category = category.value
        for key, value in category.items():
            return key in item["extras"] and item["extras"].get(key) == value
