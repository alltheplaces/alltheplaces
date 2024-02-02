import json
import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.items import Feature


class HarrisFarmMarketsAUSpider(CrawlSpider):
    name = "harris_farm_markets_au"
    item_attributes = {"brand": "Harris Farm Markets", "brand_wikidata": "Q5664888"}
    allowed_domains = ["www.harrisfarm.com.au"]
    start_urls = ["https://www.harrisfarm.com.au/pages/our-stores"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"^https:\/\/www\.harrisfarm\.com\.au\/pages\/[\w\-]+$",
                deny=r"-butcher$",
                restrict_xpaths='//div[contains(@class, "HF-new-blockstyle-card-UI")]',
            ),
            callback="parse",
        )
    ]

    def parse(self, response):
        properties = {
            "ref": response.url,
            "name": response.xpath('//div[@class="child"]/h1[@class="title"]/a/text()').get(),
            "addr_full": re.sub(
                r"\s+", " ", ", ".join(filter(None, response.xpath('//div[@id="contacts"]/p//text()').getall()))
            ),
            "phone": response.xpath(
                '//text()[contains(., "Telephone:")]/ancestor::*[self::strong][1]/ancestor::*[self::li][1]/text()'
            ).get(),
            "email": "".join(
                filter(
                    None,
                    response.xpath(
                        '//text()[contains(., "Email:")]/ancestor::*[self::strong][1]/ancestor::*[self::li][1]/a//text()'
                    ).getall(),
                )
            ),
            "website": response.url,
        }
        if properties["email"] == "hello@harrisfarm.com.au":
            properties.pop("email")
        hours_js = response.xpath('//script[contains(text(), "var openingHours = {")]/text()').get()
        hours_js = "{" + hours_js.split("var openingHours = {", 1)[1].split("}", 1)[0] + "}"
        hours_dict = json.loads(hours_js)
        hours_string = " ".join([f"{day}: {hour_range}" for day, hour_range in hours_dict.items()])
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)
        latlng = response.xpath('//script[contains(text(), "google.maps.LatLng(")]/text()').get()
        if latlng:
            properties["lat"], properties["lon"] = (
                latlng.split("google.maps.LatLng(", 1)[1].split(")", 1)[0].split(",", 1)
            )
        yield Feature(**properties)
