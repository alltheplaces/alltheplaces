from urllib.parse import urljoin

import scrapy

from locations.dict_parser import DictParser


class BricomarchePLSpider(scrapy.Spider):
    name = "bricomarche_pl"
    item_attributes = {"brand": "Bricomarché", "brand_wikidata": "Q2925147"}
    start_urls = ["https://www.bricomarche.pl/api/v1/pos/pos/poses.json"]
    requires_proxy = True  # Cloudflare bot protection used

    def parse(self, response):
        for store in response.json()["results"]:
            item = DictParser.parse(store)
            if slug := store.get("Slug"):
                item["website"] = urljoin("https://www.bricomarche.pl/sklep/", slug)
            yield item
