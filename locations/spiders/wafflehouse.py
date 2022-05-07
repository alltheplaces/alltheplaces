# -*- coding: utf-8 -*-
import json

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class WaffleHouseSpider(scrapy.Spider):
    name = "wafflehouse"
    item_attributes = {"brand": "Waffle House", "brand_wikidata": "Q1701206"}
    allowed_domains = ["wafflehouse.com"]
    start_urls = [
        "https://wafflehouse.locally.com/stores/conversion_data?has_data=true&company_id=117995&store_mode=&style=&color=&upc=&category=&inline=1&show_links_in_list=&parent_domain=&map_center_lat=39.8&map_center_lng=-98.6&map_distance_diag=3000&sort_by=proximity&no_variants=0&only_retailer_id=&dealers_company_id=&only_store_id=false&uses_alt_coords=false&zoom_level=4&lang=en-us&forced_coords=1"
    ]

    def parse(self, response):
        for row in response.json()["markers"]:
            url = "https://locations.wafflehouse.com/" + row["slug"]
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        data = json.loads(
            response.xpath('//head/script[@type="application/ld+json"]/text()').get()
        )

        hours = OpeningHours()
        specs = data.get("openingHoursSpecification", [])
        if any({"validFrom", "validThrough"} <= spec.keys() for spec in specs):
            # Giving opening hours for specific dates, abandon the whole proposal
            pass
        else:
            for spec in specs:
                for day in spec["dayOfWeek"]:
                    hours.add_range(
                        day[:2].capitalize(), spec["opens"], spec["closes"], "%I%p"
                    )

        properties = {
            "ref": data["@id"],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "website": response.url,
            "name": data["name"],
            "phone": data["telephone"],
            "street_address": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "opening_hours": hours.as_opening_hours(),
        }

        yield GeojsonPointItem(**properties)
