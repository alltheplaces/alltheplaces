import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class HomeDepotCASpider(CrawlSpider, StructuredDataSpider):
    name = "home_depot_ca"
    item_attributes = {"brand": "The Home Depot", "brand_wikidata": "Q864407"}
    allowed_domains = ["homedepot.ca"]
    start_urls = ["https://stores.homedepot.ca/"]
    rules = [
        Rule(LinkExtractor(allow=r"https://stores.homedepot.ca/\w+/$", restrict_xpaths='//*[@class="browse-wrap"]')),
        Rule(LinkExtractor(allow=r"https://stores.homedepot.ca/\w+/[a-z-\/]+/$")),
        Rule(LinkExtractor(allow=r"https://stores.homedepot.ca/\w+/[a-z-\/]+$/")),
        Rule(
            LinkExtractor(
                allow=r"https://stores.homedepot.ca/\w+/[a-z-]+/[a-z0-9-\.]+$",
                restrict_xpaths='//*[@data-show-country="en-ca"]',
            ),
            "parse_sd",
        ),
    ]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = re.search(r".+/.+?([0-9]+).html", response.url).group(1)
        item["branch"] = (
            item.pop("name")
            .replace("The Home Depot: ", "")
            .replace("Home Improvement & Hardware Store in ", "")
            .replace("Home Depot : Magasin spécialisé en amélioration domiciliaire et en quincaillerie à ", "")
            .replace(".", "")
        )

        apply_category(Categories.SHOP_DOITYOURSELF, item)

        yield item
