import re
from html import unescape

from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class LornaJaneSpider(Spider):
    name = "lorna_jane"
    item_attributes = {"brand": "Lorna Jane", "brand_wikidata": "Q28857986"}
    allowed_domains = ["www.lornajane.com.au"]
    start_urls = [
        "https://www.lornajane.com.au/on/demandware.store/Sites-LJAU-Site/en_AU/Stores-FindStores?country=AU&query=",
        "https://www.lornajane.com.au/on/demandware.store/Sites-LJAU-Site/en_AU/Stores-FindStores?country=NZ&query=",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for location in response.xpath('//div[@class="store-item container" and @data-store-id]'):
            properties = {
                "ref": location.xpath(".//@data-store-id").get(),
                "name": location.xpath(".//@data-store-name").get(),
                "addr_full": unescape(
                    re.sub(
                        r"\s+",
                        " ",
                        "".join(
                            filter(None, location.xpath('.//div[contains(@class, "store-address")]/text()').getall())
                        ),
                    )
                ).strip(),
                "phone": location.xpath('.//a[@class="storelocator-phone"]/@href').get().replace("tel:", ""),
                "website": location.xpath('.//div[contains(@class, "store-name")]/a/@href').get(),
            }
            if "CLOSED" in properties["name"].upper().split():
                continue
            if m := re.search(
                r"https:\/\/maps\.google\.com\/\?daddr=(-?\d+\.\d+),(-?\d+\.\d+)",
                location.xpath('.//a[@class="store-map"]/@href').get(),
            ):
                properties["lat"] = m.group(1)
                properties["lon"] = m.group(2)
            if "country=AU" in response.url:
                properties["country"] = "AU"
            elif "country=NZ" in response.url:
                properties["country"] = "NZ"
            hours_string = re.sub(
                r"\s+",
                " ",
                "".join(filter(None, location.xpath('.//div[contains(@class, "store-hours")]//text()').getall())),
            ).strip()
            properties["opening_hours"] = OpeningHours()
            properties["opening_hours"].add_ranges_from_string(hours_string)
            yield Feature(**properties)
