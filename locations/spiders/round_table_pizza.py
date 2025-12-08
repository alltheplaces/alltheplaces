import re

import scrapy

from locations.items import Feature


class RoundTablePizzaSpider(scrapy.Spider):
    name = "round_table_pizza"
    allowed_domains = ["www.roundtablepizza.com"]
    item_attributes = {"brand": "Round Table Pizza", "brand_wikidata": "Q7371139"}
    start_urls = ("https://ordering.roundtablepizza.com/site/rtp/locations",)

    def parse(self, response):
        for store in response.xpath('//div[@class="coordinatos"]'):
            address_search = re.search(
                r"^(.*)\s([A-Z]{2})\s?,?\s?(\d+)?$",
                store.attrib.get("data-address2").strip(),
            )
            city = state = postcode = None
            if address_search is not None:
                address_groups = address_search.groups()
                city = address_groups[0]
                state = address_groups[1]
                postcode = address_groups[2]

            yield Feature(
                lat=store.attrib.get("data-latitude"),
                lon=store.attrib.get("data-longitude"),
                name=store.attrib.get("data-name"),
                street_address=store.attrib.get("data-address1"),
                city=city,
                state=state,
                postcode=postcode,
                phone=store.attrib.get("data-phone"),
                website=store.attrib.get("data-url"),
                ref=store.attrib.get("data-companyseq"),
            )
