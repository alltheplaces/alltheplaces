import ast

import scrapy

from locations.items import Feature


class XpoLogisticsSpider(scrapy.Spider):
    name = "xpo_logistics"
    item_attributes = {"brand": "XPO Logistics", "brand_wikidata": "Q8042415"}
    allowed_domains = ["www.xpo.com"]
    start_urls = ("https://www.xpo.com/global-locations/",)

    def parse(self, response):
        script = response.xpath('//script[@id="globalLocations"]/text()').extract_first()
        data = ast.literal_eval(script)

        for store in data:
            yield Feature(
                lat=float(store["latitude"]),
                lon=float(store["longitude"].replace(",", "")),
                phone=store["telephone"],
                ref=f"{store['office_name']}-{store['postal_code']}",
                addr_full=store["street"],
                city=store["city"],
                state=store["state"],
                postcode=store["postal_code"],
                country=store["country"],
                name=store["office_name"],
            )
