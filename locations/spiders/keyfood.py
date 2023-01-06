import re

import scrapy
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class KeyfoodSpider(SitemapSpider):
    name = "keyfood"
    item_attributes = {"brand": "Key Food"}
    allowed_domains = ["keyfood.com"]
    sitemap_urls = [
        "https://www.keyfood.com/store/medias/Store-en-USD-9631859099974182222.xml?context=bWFzdGVyfHJvb3R8Njg4NjN8dGV4dC94bWx8aGYwL2hmMS85NzI0MDI4MzIxODIyL1N0b3JlLWVuLVVTRC05NjMxODU5MDk5OTc0MTgyMjIyLnhtbHxmYjY3MDI4OGYyYmZiYjc4NWM0YmU5NjQ1ZjQwMWRiYzU3NTExNjUxOTEwYmE1NzU2ZTU4OTIwODY0NzQ4YTI0"
    ]
    sitemap_rules = [("", "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def _parse_sitemap(self, response):
        for row in super()._parse_sitemap(response):
            lat, lon = re.findall(r"-{0,1}\d+.\d+", row.url)[-2:]
            url = f"https://keyfoodstores.keyfood.com/store/keyFood/en/store-locator?q={lat},{lon}&page=0&radius=1&all=false"
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                cb_kwargs={"store_url": row.url},
            )

    def parse(self, response, store_url):
        data = response.json().get("data")[0]
        item = DictParser.parse(data)
        item["ref"] = data.get("name")
        item["name"] = data.get("displayName")
        item["website"] = store_url
        oh = OpeningHours()
        if data.get("openings"):
            for day, value in data.get("openings").items():
                if value == "Open 24 hours":
                    value = "12:00 AM - 12:00 AM"
                oh.add_range(
                    day=day,
                    open_time=value.split(" - ")[0],
                    close_time=value.split(" - ")[1],
                    time_format="%I:%M %p",
                )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
