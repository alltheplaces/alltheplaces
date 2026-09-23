import re
from datetime import datetime
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class PancherosUSSpider(Spider):
    name = "pancheros_us"
    item_attributes = {
        "brand": "Pancheros",
        "brand_wikidata": "Q7130313",
        "name": "Pancheros Mexican Grill",
    }
    start_urls = ["https://pancheros.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.css("div.location"):
            item = Feature()
            item["ref"] = location.attrib["data-id"]
            item["lat"] = location.attrib["data-lat"]
            item["lon"] = location.attrib["data-long"]

            name = location.css("h4::text").get("")
            item["branch"] = re.sub(r"^Pancheros\s*–\s*", "", name).strip()

            address_lines = location.css(".details > p")[0].css("::text").getall()
            item["street_address"] = address_lines[0].strip()
            if m := re.match(r"^(.+), ([A-Z]{2}) (\d{5}(?:-\d{4})?)$", address_lines[1].strip()):
                item["city"], item["state"], item["postcode"] = m.groups()

            item["phone"] = location.css(".details > p")[1].css("::text").get()

            href = location.css('a[href^="/location/"]::attr(href)').get()
            item["website"] = response.urljoin(href)

            apply_category(Categories.RESTAURANT, item)
            supports = location.css("p.supports::text").get("")
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in supports)

            yield response.follow(item["website"], callback=self.parse_hours, cb_kwargs={"item": item})

    def parse_hours(self, response: Response, item: Feature) -> Any:
        oh = OpeningHours()
        for day_row in response.css(".hours .days > div"):
            texts = day_row.css("p::text").getall()
            if len(texts) != 2:
                continue
            day, hours = texts
            if m := re.match(r"^([\d:]+)\s*([ap]m)\s*–\s*([\d:]+)\s*([ap]m)$", hours.strip(), re.I):
                open_h, open_ap, close_h, close_ap = m.groups()
                open_time = datetime.strptime(f"{open_h}{open_ap}", "%I:%M%p").strftime("%H:%M")
                close_time = datetime.strptime(f"{close_h}{close_ap}", "%I:%M%p").strftime("%H:%M")
                oh.add_range(day.strip(), open_time, close_time)
        item["opening_hours"] = oh

        yield item
