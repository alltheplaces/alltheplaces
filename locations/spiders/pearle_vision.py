import re

import scrapy
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class PearleVisionSpider(SitemapSpider):
    name = "pearle_vision"
    item_attributes = {"brand": "Pearle Vision", "brand_wikidata": "Q2231148"}
    allowed_domains = ["pearlevision.com", "www.pearlevision.ca"]
    sitemap_urls = ["https://www.pearlevision.com/sitemap-store-locations.xml"]
    sitemap_rules = [(r"/stores/\w{2}/[-\w]+/\d+", "parse")]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "*/*",
            "User-Agent": BROWSER_DEFAULT,
            "Connection": "keep-alive",
            "Accept-Encoding": "gzip, deflate, br",
        },
    }

    def find_between(self, text, first, last):
        start = text.index(first) + len(first)
        end = text.index(last, start)
        return text[start:end]

    def _parse_sitemap(self, response):
        for row in super()._parse_sitemap(response):
            yield scrapy.Request(row.url.strip("/"), callback=self.parse)

    def parse(self, response):
        if url := response.xpath('//iframe[@id="brandHeader"]/@src').get():
            hours = (
                self.find_between(response.text, "var storeHoursRaw = siteHour ? [", "] :")
                .replace("\r\n", "")
                .replace(" ", "")
                .replace('"', "")
                .replace("'", "")
                .split(",")
            )
            days = self.find_between(response.text, "var days = [", "]").replace(" ", "").replace('"', "").split(",")
            opening_hours = [f"{days[i]} {hours[i]}" for i in range(len(days)) if hours[i] != "-"]
            oh = OpeningHours()
            oh.from_linked_data({"openingHours": opening_hours}, "%I:%M%p")

            yield scrapy.Request(
                url=url,
                callback=self.pares_store,
                cb_kwargs={"website": response.url, "opening_hours": oh.as_opening_hours()},
            )

    def pares_store(self, response, website, opening_hours):
        item = Feature()
        data = response.xpath('//script/text()[contains(., "var storeName")]').get()
        item["name"] = self.find_between(data, 'var storeName = "', '".trim();').strip()
        item["street_address"] = self.find_between(data, 'var address = "', '".trim();').strip()
        item["state"] = self.find_between(data, 'var state = "', '".trim();').strip().upper()
        item["postcode"] = self.find_between(data, 'var zipCode = "', '".trim();').strip()
        item["phone"] = self.find_between(data, 'var telephone = "', '".trim();').strip()
        item["lat"] = self.find_between(data, 'var latitude = "', '".trim();').strip()
        item["lon"] = self.find_between(data, 'var longitude = "', '".trim();').strip()
        item["website"] = website
        item["ref"] = re.findall("[0-9]+$", website)[0]
        item["opening_hours"] = opening_hours

        yield item
