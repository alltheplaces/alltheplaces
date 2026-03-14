import re

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class PresbyterianChurchCASpider(scrapy.Spider):
    name = "presbyterian_church_ca"
    item_attributes = {"operator": "Presbyterian Church in Canada", "operator_wikidata": "Q3586082"}
    start_urls = ["https://presbyterian.ca/churchlocator/demo/final.html"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs):
        for store_div in response.xpath('//div[@data-type="store"]'):
            yield self.parse_store(store_div)

    def parse_store(self, store_div):

        item = Feature()

        church_name = store_div.xpath('.//*[@data-type="title"]/text()').get()
        # Remove any city context in brackets from the name.
        item["name"] = re.sub(r" \([^)]*\)", "", church_name).strip()

        item["ref"] = store_div.xpath('.//*[@data-type="congid"]//text()').get()
        item["lat"] = store_div.xpath("./@data-latitude").get()
        item["lon"] = store_div.xpath("./@data-longitude").get()

        if addr_full := store_div.xpath('.//*[@data-type="address"]/text()').get():
            item["addr_full"] = addr_full
            if postal_match := re.search(r"\b([A-Z]\d[A-Z]\s?\d[A-Z]\d)\b", addr_full):
                item["postcode"] = postal_match.group(1)

        if phone := store_div.xpath('.//*[@data-type="Phone"]/text()').get():
            # Remove all non-numeric characters, pipeline handles the rest
            item["phone"] = re.sub(r"\D", "", phone)

        # Look for a website
        for url in store_div.xpath(".//@href"):
            if url.get().startswith("http"):
                item["website"] = url.get()
                break

        apply_category(Categories.PLACE_OF_WORSHIP, item)
        item["extras"]["religion"] = "christian"
        item["extras"]["denomination"] = "presbyterian"

        return item
