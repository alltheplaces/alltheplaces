from typing import Iterable

import scrapy
from requests_cache import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class HsbcTWSpider(StructuredDataSpider):
    name = "hsbc_tw"
    item_attributes = {"brand": "HSBC", "brand_wikidata": "Q5635861"}
    start_urls = ["https://www.hsbc.com.tw/en-tw/ways-to-bank/branch/"]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if ld_obj.get("address"):  # @type key is not present for the desired ld_data
                yield ld_obj

    def parse(self, response: Response, **kwargs):
        for branch in response.xpath(r'//*[@class="desktop"]//td[2]').xpath("normalize-space()").getall():
            url = "https://www.hsbc.com.tw/en-tw/branch-list/" + branch.lower().replace(
                "taoyuan branch", "tahsin branch"
            ).replace(" (bilingual branch)", "").replace(" ", "-")
            yield scrapy.Request(url=url, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("HSBC - ").removesuffix(" Branch")
        for service in ld_data["hasOfferCatalog"]["itemListElement"]:
            apply_yes_no(Extras.ATM, item, "atm" in service["itemOffered"]["name"].lower())

        apply_category(Categories.BANK, item)

        yield item
