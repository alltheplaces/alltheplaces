import re
from typing import AsyncIterator, Iterable

from scrapy.http import FormRequest, Request, Response, TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# 2024-02-18 Sitemap is out of date, and before we access /getStoreList we need a legit ci_session cookie


class SalvatoreCASpider(CrawlSpider, StructuredDataSpider):
    name = "salvatore_ca"
    item_attributes = {"brand_wikidata": "Q121738133"}
    rules = [Rule(LinkExtractor("/en/restaurant/"), "parse_sd")]
    wanted_types = ["Restaurant"]

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://salvatore.com/en/restaurant", callback=self.parse_page)

    def parse_page(self, response: Response, **kwargs):
        yield FormRequest(
            url="https://salvatore.com/getStoreList", formdata={"geoloca": "false", "tz": "UTC"}, callback=self._parse
        )

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Pizza Salvatoré ")
        if m := re.match(r"(\w\w) (\w\d\w \d\w\d)", (ld_data.get("address") or {}).get("addressRegion")):
            item["state"], item["postcode"] = m.groups()

        item["website"] = response.xpath('//link[@rel="canonical"]/@href').get()
        item["extras"]["website:fr"] = response.xpath('//link[@rel="alternate"][@hreflang="fr"]/@href').get()
        item["extras"]["website:en"] = response.xpath('//link[@rel="alternate"][@hreflang="en"]/@href').get()

        apply_category(Categories.FAST_FOOD, item)

        yield item
