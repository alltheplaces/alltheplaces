import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class CantinaLaredoUSSpider(Spider):
    name = "cantina_laredo_us"
    item_attributes = {"brand": "Cantina Laredo"}
    start_urls = ["https://www.cantinalaredo.com/locations/"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.css(".single-location"):
            website = response.urljoin(location.css(".location-visit a::attr(href)").get())
            branch, state = location.css(".location-name").xpath("normalize-space(.)").get().rsplit(",", 1)
            address = location.css(".location-address").xpath("normalize-space(.)").get()
            item = Feature(
                ref=website.rstrip("/").rsplit("/", 1)[-1],
                branch=branch.strip(),
                addr_full=address,
                state=state.strip(),
                postcode=re.search(r"\b[A-Z]{2}\s+(\d{5})\b", address).group(1),
                country="US",
                phone=location.css(".tel a::text").get(),
                website=website,
            )
            hours_text = " ".join(location.css(".hours p").xpath(".//text()").getall())
            if "departure" not in hours_text.lower():
                hours = OpeningHours()
                if "7 days a week" in hours_text:
                    hours_text = "Mo-Su " + hours_text.split(",", 1)[0]
                hours.add_ranges_from_string(hours_text.replace("Fri & Sat", "Fri-Sat"))
                item["opening_hours"] = hours
            apply_category(Categories.RESTAURANT, item)
            yield item
