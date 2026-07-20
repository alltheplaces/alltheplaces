from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class HygieiaPLSpider(Spider):
    name = "hygieia_pl"
    item_attributes = {"brand": "Hygieia", "brand_wikidata": "Q122906354"}
    allowed_domains = ["www.hygieia.pl"]
    start_urls = ["https://www.hygieia.pl/apteki/"]
    no_refs = True

    def parse(self, response: Response) -> Iterable[Feature]:
        for store in response.xpath('//*[contains(@class," mfn-module-wrapper mfn-wrapper-for-wraps")]'):
            if title := store.xpath(".//h4/text()").get():
                item = Feature()
                item["street_address"] = title
                item["addr_full"] = merge_address_lines([item["street_address"], store.xpath(".//p/text()").get()])
                item["phone"] = store.xpath('.//*[contains(@href,"tel:")]/@href').get().replace("tel:", "")
                item["email"] = store.xpath('.//*[contains(@href,"mailto:")]/@href').get().replace("mailto:", "")
                apply_category(Categories.PHARMACY, item)
                yield item
