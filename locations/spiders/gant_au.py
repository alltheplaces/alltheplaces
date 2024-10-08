from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class GantAUSpider(Spider):
    name = "gant_au"
    item_attributes = {"brand": "GANT", "brand_wikidata": "Q1493667"}
    allowed_domains = ["gant.com.au"]
    start_urls = ["https://gant.com.au/pages/stores"]

    def parse(self, response):
        for location in response.xpath('//div[contains(@class, "stores-data")]/div'):
            properties = {
                "ref": location.xpath('./p[@class = "name"]/text()')
                .get()
                .replace('"', "")
                .replace(" ", "_")
                .lower()
                .strip(),
            }
            field_map = {
                "state": "state",
                "name": "name",
                "address": "addr_full",
                "phone": "phone",
                "coords-lat": "lat",
                "coords-long": "lon",
            }
            for field_source, field_mapped in field_map.items():
                properties[field_mapped] = (
                    location.xpath(f'./p[@class = "{field_source}"]/text()').get().replace('"', "").strip()
                )
            properties["opening_hours"] = OpeningHours()
            hours_string = location.xpath('./p[@class = "hours"]/text()').get().replace('"', "").replace("\n", " ")
            properties["opening_hours"].add_ranges_from_string(hours_string)
            yield Feature(**properties)
