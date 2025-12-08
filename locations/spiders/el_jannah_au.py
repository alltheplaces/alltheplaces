import re

from scrapy import Spider

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature


class ElJannahAUSpider(Spider):
    name = "el_jannah_au"
    item_attributes = {"brand": "El Jannah", "brand_wikidata": "Q96377069", "extras": Categories.FAST_FOOD.value}
    allowed_domains = ["eljannah.com.au"]
    start_urls = ["https://eljannah.com.au/locations/"]

    def parse(self, response):
        js_blob = response.xpath('//script[contains(text(), "let locations_")]/text()').get()
        # Extract all four fields from example of:
        # [2574,'Albion Park', '-34.556885082830945', '150.7914680932255']
        locations_geodata_raw = re.findall(
            r"\[\s*(\d+)\s*\,\s*'\s*([^']+)\s*'\s*\,\s*'\s*(-?\d{2,3}\.\d+)\s*'\s*\,\s*'\s*(-?\d{2,3}\.\d+)\s*'\s*\]",
            js_blob,
        )
        locations_geodata_dict = {x[0]: (x[1], float(x[2]), float(x[3])) for x in locations_geodata_raw}

        for location in response.xpath('//div[@class="location-item"]'):
            properties = {
                "ref": location.xpath("./div[1]/@data-key").get(),
                "name": location.xpath('./div[1]/h5[contains(@class, "line-item-title")]/text()').get("").strip(),
                "addr_full": location.xpath(
                    './div[1]/div[@class="location-item-row"][1]/div[@class="location-item-text"]/text()'
                )
                .get("")
                .strip(),
                "opening_hours": OpeningHours(),
            }
            properties["lat"] = locations_geodata_dict[properties["ref"]][1]
            properties["lon"] = locations_geodata_dict[properties["ref"]][2]
            hours_string = " ".join(
                filter(
                    None,
                    map(
                        str.strip,
                        location.xpath(
                            './div[1]/div[@class="location-item-row"][2]/div[@class="location-item-text"]//text()'
                        ).getall(),
                    ),
                )
            )
            properties["opening_hours"].add_ranges_from_string(hours_string)
            yield Feature(**properties)
