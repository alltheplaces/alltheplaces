import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class FleetFeetUSSpider(Spider):
    name = "fleet_feet_us"
    item_attributes = {"brand": "Fleet Feet", "brand_wikidata": "Q117062761"}
    start_urls = ["https://www.fleetfeet.com/locations"]
    no_refs = True

    def parse(self, response, **kwargs):
        for location in response.xpath('//div[@class="location"]'):
            item = Feature()
            item["lat"] = location.xpath("./@data-lat").get()
            item["lon"] = location.xpath("./@data-lng").get()
            item["branch"] = location.xpath("./h3//text()").get("").strip() or None

            addr_lines = [s.strip() for s in location.xpath('./p[@class="address"]/text()').getall() if s.strip()]
            city_idx = None
            for i, line in enumerate(addr_lines):
                if m := re.match(r"^(.+),\s*([A-Z]{2})\s+(\d{5})$", line):
                    item["city"] = m.group(1).strip()
                    item["state"] = m.group(2)
                    item["postcode"] = m.group(3)
                    city_idx = i
                    break
            if city_idx is not None and city_idx > 0:
                item["street_address"] = merge_address_lines(addr_lines[:city_idx])

            apply_category(Categories.SHOP_SHOES, item)

            yield item
