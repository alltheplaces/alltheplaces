from html import unescape
from json import loads
from typing import Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class CitiwoodZASpider(Spider):
    name = "citiwood_za"
    item_attributes = {
        "brand": "Citiwood",
        "brand_wikidata": "Q130407139",
    }
    allowed_domains = ["citiwood.co.za"]
    start_urls = ["https://citiwood.co.za/contacts/"]
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        locations = loads(unescape(response.xpath('//div[@class="mdp-gmaper-elementor-box"]/@data-markers').get()))
        for location in locations:
            properties = {
                "branch": location["pin_item_title"].removeprefix("Citiwood "),
                "lat": location["pin_latitude"],
                "lon": location["pin_longitude"],
                "addr_full": merge_address_lines(
                    filter(
                        lambda x: x not in ["Get Directions", "Address"],
                        Selector(text=location["pin_item_description"]).xpath("//text()").getall(),
                    )
                ).strip(" :"),
            }
            apply_category(Categories.SHOP_TRADE, properties)
            yield Feature(**properties)
