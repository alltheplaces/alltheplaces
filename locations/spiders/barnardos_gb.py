import re
from urllib.parse import unquote

from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature


class BarnardosGBSpider(Spider):
    name = "barnardos_gb"
    item_attributes = {"brand": "Barnardos", "brand_wikidata": "Q2884670"}

    def start_requests(self):
        yield JsonRequest(
            url="https://shop.barnardos.org.uk/api/StoreLocator/RetrieveNearest",
            data={
                "Origin": "0,0",
                "DistanceType": "StraightLine",
                "LocationLists": "Barnardos Stores",
                "StoreFinder": "StoreFinder",
            },
        )

    def parse(self, response, **kwargs):
        for poi in response.json():
            item = Feature()
            item["ref"] = poi.get("yourId")
            item["branch"] = poi.get("name").replace("+", " ")
            item["lat"] = poi["latitude"]
            item["lon"] = poi["longitude"]
            poi["description"] = unquote(poi["description"]).replace("+", " ").replace("</br>", " ")
            selector = Selector(text=poi["description"])

            item["phone"] = selector.xpath('//*[contains(text(), "Contact")]/following-sibling::p/text()').get()

            addr_lines = " ".join(
                selector.xpath('//*[contains(text(), "Address")]/following-sibling::p//text()').getall()
            )
            item["addr_full"] = re.sub(r"\s+", " ", addr_lines)

            item["opening_hours"] = OpeningHours()
            for start_day, end_day, open_time, close_time in re.findall(
                r"(?:(\w+)[-\s]+)?(\w+)[:\s]+(\d+:\d+)[-\s]+(\d+:\d+)", poi["description"]
            ):
                end_day = sanitise_day(end_day)
                start_day = sanitise_day(start_day) or end_day
                if start_day:
                    item["opening_hours"].add_days_range(day_range(start_day, end_day), open_time, close_time)

            item["website"] = (
                "https://shop.barnardos.org.uk" + selector.xpath('//a[contains(@class, "btn")]/@href').get()
            )

            yield item
