# -*- coding: utf-8 -*-
import json
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from locations.brands import Brand
from locations.seo import extract_details, join_address_fields


class TimpsonUKSpider(CrawlSpider):
    name = "timpson_uk"
    brand = Brand.from_wikidata("Timpson", "Q7807658")
    start_urls = ["https://www.timpson.co.uk/stores/"]
    rules = [Rule(LinkExtractor(allow="stores/"), callback="parse_func", follow=True)]

    def parse_func(self, response):
        return self.extract(self.brand, response)

    @staticmethod
    def extract(my_brand, response):
        pattern = re.compile(r"var lpr_vars = ({.*?})\n", re.MULTILINE | re.DOTALL)
        for lpr_var in response.xpath(
            '//script[contains(., "var lpr_vars")]/text()'
        ).re(pattern):
            store = json.loads(lpr_var)
            details = store["initial_location"]
            if type(details) is type(store):
                item = my_brand.item(response)
                item["street_address"] = join_address_fields(
                    details, "street1", "street2"
                )
                yield extract_details(item, details)
