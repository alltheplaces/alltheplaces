# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class GulfSpider(scrapy.Spider):
    name = "gulf"
    item_attributes = {"brand": "Gulf Oil", "brand_wikidata": "Q5617505"}
    allowed_domains = ["gulfoil.com"]

    start_urls = [
        "https://www.gulfoil.com/views/ajax?field_geofield_distance%5Bdistance%5D=90000&field_geofield_distance%5Bunit%5D=3959&field_geofield_distance%5Borigin%5D=lebanon,%20ks&view_name=station_locator_block&view_display_id=block"
    ]

    def parse(self, response):
        page = response.meta.get("page", 0)
        json_result = response.json()
        html_result = json_result[-1]["data"]
        results = scrapy.Selector(text=html_result)

        for tbody in results.xpath("//tbody"):
            name = tbody.xpath("tr[1]/th[1]//text()").get()
            contact = (
                results.xpath("//tbody")[0].xpath("tr[2]/td[1]/p/text()").extract()
            )
            address = ", ".join([r.strip() for r in contact[:2]])
            phone = contact[2].replace("Phone Number: ", "")
            html_content = tbody.get()

            yield GeojsonPointItem(
                ref=name,
                name=name,
                addr_full=address,
                phone=phone,
                extras={
                    "amenity:fuel": True,
                    "fuel:diesel": "Diesel" in html_content or None,
                    "amenity:toilets": "Restrooms" in html_content or None,
                    "atm": "ATM" in html_content or None,
                },
            )

        if results.xpath("//li[@class='pager-next']/a"):
            yield scrapy.Request(
                f"{self.start_urls[0]}&page={page + 1}", meta={"page": page + 1}
            )
