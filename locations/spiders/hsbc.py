from typing import Iterable

from requests_cache import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class HSBCSpider(CrawlSpider, StructuredDataSpider):
    name = "hsbc"
    item_attributes = {"brand": "HSBC", "brand_wikidata": "Q190464", "extras": Categories.BANK.value}
    start_urls = [
        "https://www.hsbc.com.ar/branch-list/",
        "https://www.hsbc.am/en-am/branch-list/",
        "https://www.hsbc.com.au/branch-list/",
        # "https://www.hsbc.com.bh/branch-finder/",
        # "https://www.hsbc.com.bd/1/2/home",
        "https://www.hsbc.bm/branch-list/",
        "https://www.hsbc.ca/branch-list/",
        # "https://www.hsbc.com.eg/branch-finder/",
        # "https://branches.hsbc.fr/",
        "https://www.hsbc.gr/en-gr/branch-list/",
        "https://ciiom.hsbc.com/branch-list/",
        "https://www.hsbc.com.hk/branch-list/",
        "https://www.hsbc.co.in/branch-list/",
        # "https://www.hsbc.co.id/1/2/en/branch-locator",
        "https://www.hsbc.com.mo/branch-list/",
        # "https://www.hsbc.com.cn/en-cn/",
        "https://www.hsbc.com.my/branch-list/",
        "https://www.hsbc.com.mt/branch-list/",
        "https://www.hsbc.co.mu/branch-list/",
        # "https://www.hsbc.com.mx/contacto/directorio-de-sucursales/",
        # "https://www.hsbc.co.nz/",
        # "https://www.oman.hsbc.com/",
        "https://www.hsbc.com.ph/branch-list/",
        # "https://www.hsbc.com.qa/",
        # "https://www.sabb.com/en/",
        "https://www.hsbc.com.sg/branch-list/",
        "https://www.hsbc.lk/branch-list/",
        # "https://www.hsbc.com.tw/en-tw/",
        # "https://www.hsbc.com.tr/en/branches-and-atms/branches-and-atms",
        # "https://www.hsbc.ae/branch-finder/",
        # "https://www.hsbc.co.uk/", # HSBCUKGBSpider
        # "https://www.hsbc.com.uy/",
        # "https://www.us.hsbc.com/wealth-center/list/", # HSBCUSSpider
        # "https://www.hsbc.com.vn/en-vn/contact/branch-finder/",
    ]
    rules = [Rule(LinkExtractor(allow="/branch-list/"), callback="parse_sd")]

    # TODO: Remove this method when the types will be added to structured data
    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if not ld_obj.get("@type"):
                # Structured data for bank branches on all pages does not have a type currently,
                # so we're overriding iter_linked_data to parse POIs.
                # When the type will be added, this method should still pick POIs up.
                yield ld_obj
                break

            types = ld_obj["@type"]

            if not isinstance(types, list):
                types = [types]

            types = [LinkedDataParser.clean_type(t) for t in types]

            for wanted_types in self.wanted_types:
                if isinstance(wanted_types, list):
                    if all(wanted in types for wanted in wanted_types):
                        yield ld_obj
                elif wanted_types in types:
                    yield ld_obj
