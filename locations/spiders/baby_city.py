from typing import Dict

import scrapy
from scrapy.selector import Selector

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BabyCitySpider(scrapy.Spider):
    name = "baby_city"
    item_attributes = {"brand": "Baby City", "brand_wikidata": "Q116732888"}
    allowed_domains = ["www.babycity.co.za"]

    def start_requests(self):
        yield scrapy.Request(
            url="https://www.babycity.co.za/amlocator/index/ajax/",
            method="POST",
            headers={
                "X-Requested-With": "XMLHttpRequest",
            },
            body="lat=0&lng=0&radius=0&product=0&category=0&sortByDistance=1",
        )

    def parse(self, response):
        opening_hours_map = self.parse_opening_hours(response.json()["block"])

        for i in response.json()["items"]:
            item = DictParser.parse(i)
            html = Selector(text=i["popup_html"])
            item["name"] = html.xpath('//div[@class="amlocator-title"]/text()').get()
            item["email"] = html.xpath("//a[starts-with(@href, 'mailto:')]").attrib["href"].removeprefix("mailto:")
            item["phone"] = html.xpath("//a[starts-with(@href, 'tel:')]").attrib["href"].removeprefix("tel:")

            address = html.xpath('//div[@class="amlocator-info-popup"]/text()')
            for a in address:
                a = a.get().strip()
                if a.startswith("Postal Code"):
                    _, postcode = a.split(":", maxsplit=1)
                    item["postcode"] = postcode.strip()
                elif a.startswith("City"):
                    _, city = a.split(":", maxsplit=1)
                    item["city"] = city.strip()
                elif a.startswith("State"):
                    _, state = a.split(":", maxsplit=1)
                    item["state"] = state.strip()
                elif a.startswith("Address"):
                    _, street_address = a.split(":", maxsplit=1)
                    item["street_address"] = street_address.strip().rstrip(",")

            item["opening_hours"] = opening_hours_map.get(str(item["ref"]))

            yield item

    @staticmethod
    def parse_opening_hours(html: str) -> Dict[str, OpeningHours]:
        hours_map = {}
        for x in Selector(text=html).xpath('//div[@class="amlocator-store-desc"]'):
            _id = x.xpath("@data-amid").get()
            oh = OpeningHours()
            hours = " ".join(x.xpath('.//div[@class="amlocator-schedule-table"]//text()').getall())
            oh.add_ranges_from_string(hours)
            hours_map[_id] = oh
        return hours_map
