import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.items import Feature


class TigerWheelAndTyreZASpider(CrawlSpider):
    name = "tiger_wheel_and_tyre_za"
    item_attributes = {"brand": "Tiger Wheel & Tyre", "brand_wikidata": "Q120762656"}
    start_urls = ["https://twtinfo.goreview.co.za/store-locator"]
    rules = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/twt\d+\.goreview\.co\.za\/store-information\?store-locator=twtinfo$"),
            callback="parse",
        )
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        properties = {
            "ref": response.url,
            "addr_full": re.sub(
                r"\s+",
                " ",
                ", ".join(
                    filter(
                        None,
                        map(
                            str.strip,
                            response.xpath(
                                '//div[contains(@class, "content-wrapper")]/div[2]/div[1]//p/text()'
                            ).getall(),
                        ),
                    )
                ),
            ),
            "phone": response.xpath(
                '//div[contains(@class, "content-wrapper")]/div[2]/div[3]//a[contains(@href, "tel:")]/@href'
            )
            .get()
            .replace("tel:", ""),
            "facebook": response.xpath(
                '//div[contains(@class, "content-wrapper")]/div[2]/div[5]//a[contains(@href, "facebook.com")]/@href'
            ).get(),
            "website": response.url,
        }
        if maps_links_js := response.xpath('//script[contains(text(), "#apple_maps_directions")]/text()').get():
            if "&sll=" in maps_links_js:
                properties["lat"], properties["lon"] = maps_links_js.split("&sll=", 1)[1].split("&", 1)[0].split(",", 2)
        hours_string = " ".join(
            response.xpath('//div[contains(@class, "content-wrapper")]/div[2]/div[4]/p//text()').getall()
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string)
        yield Feature(**properties)
