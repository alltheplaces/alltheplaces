import json
from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class FonehouseGBSpider(CrawlSpider, StructuredDataSpider):
    name = "fonehouse_gb"
    item_attributes = {
        "brand": "fonehouse",
        "brand_wikidata": "Q130535827",
        "country": "GB",
    }

    start_urls = ["https://www.fonehouse.co.uk/store-finder"]
    rules = [Rule(LinkExtractor(allow=r"/stores/([^/]+)$"), callback="parse_sd")]
    wanted_types = ["LocalBusiness"]

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        # The ld+json blob has a stray trailing comma after the JSON object, which
        # breaks strict JSON (and json5/chompjs) parsing, so decode just the object.
        for text in response.xpath('//script[@type="application/ld+json"]//text()').getall():
            try:
                ld_obj, _ = json.decoder.JSONDecoder(strict=False).raw_decode(text, text.index("{"))
            except (ValueError, json.JSONDecodeError):
                continue

            types = ld_obj.get("@type")
            if not types:
                continue
            if not isinstance(types, list):
                types = [types]
            types = [LinkedDataParser.clean_type(t) for t in types]

            for wanted_types in self.wanted_types:
                if isinstance(wanted_types, list):
                    if all(wanted in types for wanted in wanted_types):
                        yield ld_obj
                elif wanted_types in types:
                    yield ld_obj

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = item["website"] = response.url
        item["branch"] = item.pop("name").removeprefix("Fonehouse").strip()
        item["country"] = "GB"
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
