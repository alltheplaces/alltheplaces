import json

import scrapy

from locations.items import Feature


class FitActiveSpider(scrapy.Spider):
    name = "fit_active"
    item_attributes = {"brand": "FitActive", "brand_wikidata": "Q123807531"}
    start_urls = ["https://www.fitactive.it/Club/Club"]

    def parse(self, response):
        # Website and phone number are in a separate section of the website
        website = {}
        phone = {}
        for item in response.xpath('//ul[@class="menu-club"]/li'):
            link = item.xpath('descendant::a[not(contains(@href, "tel:"))]')
            name = link.xpath("descendant::text()").extract_first()
            website[name] = link.attrib["href"]
            phone[name] = item.xpath('descendant::a[contains(@href, "tel:")]/text()').extract_first()
        # The main information is in a JavaScript call
        javascript = response.xpath(
            '//script[@type="text/javascript" and contains(text(), "mainMap(")]/text()'
        ).re_first("mainMap\((.*)\);")
        map_data = json.loads(javascript)
        for shop in map_data:
            name = shop["title"]
            yield Feature(
                {
                    "ref": shop["id"],
                    "name": name,
                    "addr_full": shop["address"].strip(),
                    "country": shop["state"],
                    "lat": shop["latitude"],
                    "lon": shop["longitude"],
                    "email": shop["email"],
                    "phone": phone[name],
                    "website": response.urljoin(website[name]),
                }
            )
