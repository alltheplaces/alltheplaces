import json
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from locations.dict_parser import DictParser


class TimpsonGBSpider(CrawlSpider):
    name = "timpson_gb"
    item_attributes = {"brand": "Timpson", "brand_wikidata": "Q7807658"}
    start_urls = ["https://www.timpson.co.uk/stores/"]
    rules = [Rule(LinkExtractor(allow="stores/"), callback="parse_func", follow=True)]
    download_delay = 0.5

    def parse_func(self, response):
        return self.extract(response)

    @staticmethod
    def extract(response):
        pattern = re.compile(r"var lpr_vars = ({.*?})\n", re.MULTILINE | re.DOTALL)
        for lpr_var in response.xpath(
            '//script[contains(., "var lpr_vars")]/text()'
        ).re(pattern):
            store = json.loads(lpr_var)
            details = store["initial_location"]
            if type(details) is type(store):
                item = DictParser.parse(details)
                item["website"] = response.url
                if item.get("country") == "Ireland":
                    item["country"] = "IE"
                else:
                    item["country"] = "GB"
                item["street_address"] = join_address_fields(
                    details, "street1", "street2"
                )

                # TODO: too painful to port at present
                # for brand in [Brand.MORRISONS, Brand.SAINSBURYS, Brand.TESCO, Brand.ASDA, Brand.WAITROSE]:
                #     if brand.name().replace('\'s', '').lower() in response.url.lower():
                #         item.set_located_with(brand)
                return item


def join_address_fields(src, *fields):
    """
    Pull referenced fields from the src and form a clean address string assuming comma separated address.
    Tolerant of missing and empty fields.
    """
    dirty = []
    for field in fields:
        dirty.append(src.get(field))
    return join_address_array(dirty)


def join_address_array(address_array, join_str=","):
    """
    Attempt to "clean" an array of address items returning a single string address.
    """
    address_array = list(filter(lambda s: s and len(s.strip()) > 0, address_array))
    all_parts = join_str.join(address_array).split(join_str)
    all_parts = list(filter(lambda s: s and len(s.strip()) > 0, all_parts))
    all_parts = list(map(lambda s: s.strip(), all_parts))
    for i in range(0, len(all_parts)):
        for j in range(i + 1, len(all_parts)):
            # Remove duplicate consecutive entries
            if (
                all_parts[i]
                and all_parts[j]
                and all_parts[i].lower() == all_parts[j].lower()
            ):
                all_parts[i] = None
    all_parts = list(filter(lambda s: s, all_parts))
    join_str = join_str + " "
    return join_str.join(all_parts)
