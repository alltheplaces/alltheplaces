import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class GdkSpider(scrapy.Spider):
    name = "gdk"
    item_attributes = {"brand": "German Doner Kebab", "brand_wikidata": "Q112913418"}
    start_urls = [
        "https://www.gdk.com/gb/gdk-locations",
        "https://www.gdk.com/ie/gdk-locations",
        "https://www.gdk.com/se/gdk-locations",
        "https://www.gdk.com/ae/gdk-locations",
        "https://www.gdk.com/sa/gdk-locations",
    ]

    def parse(self, response, **kwargs):
        data = response.xpath("//div[contains(@class, 'location-item')]")
        for location in data:
            item = Feature()
            item["branch"] = location.xpath(".//h3//text()").get()
            item["country"] = re.search(r"https://www.gdk.com/(\w+)/", response.url).group(1)
            if location.xpath(".//a[contains(@href, 'https://www.google.com/maps')]//@href"):
                item["addr_full"] = (
                    location.xpath(".//a[contains(@href, 'https://www.google.com/maps/dir/Current+Location/')]//@href")
                    .get()
                    .rstrip()
                    .replace("https://www.google.com/maps/dir/Current+Location/", "")
                    .replace("\r", ",")
                    .replace("German Doner Kebab+", "")
                )
            else:
                continue
            item["name"] = "German Doner Kebab"
            if website := location.xpath('.//*[contains(text(),"MORE INFO")]/@href').get():
                item["website"] = website
            item["ref"] = location.xpath('.//*[contains(text(),"DIRECTIONS")]/@href').get()
            apply_category(Categories.FAST_FOOD, item)
            yield item
