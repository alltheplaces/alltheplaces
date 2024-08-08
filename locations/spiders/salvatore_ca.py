from typing import Iterable

from scrapy import FormRequest, Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

# 2024-02-18 Sitemap is out of date, and before we access /getStoreList we need a legit ci_session cookie


class SalvatoreCASpider(CrawlSpider, StructuredDataSpider):
    name = "salvatore_ca"
    item_attributes = {"brand_wikidata": "Q121738133"}
    rules = [Rule(LinkExtractor("/en/restaurant/"), "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]

    def start_requests(self) -> Iterable[Request]:
        yield Request("https://salvatore.com/en/restaurant", callback=self.parse_page)

    def parse_page(self, response: Response, **kwargs):
        yield FormRequest(
            url="https://salvatore.com/getStoreList", formdata={"geoloca": "false", "tz": "UTC"}, callback=self._parse
        )

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        item["addr_full"] = item.pop("street_address")
        item["lat"], item["lon"] = item["lon"], item["lat"]

        item["website"] = response.xpath('//link[@rel="canonical"]/@href').get()
        item["extras"]["website:fr"] = response.xpath('//link[@rel="alternate"][@hreflang="fr"]/@href').get()
        item["extras"]["website:en"] = response.xpath('//link[@rel="alternate"][@hreflang="en"]/@href').get()

        apply_category(Categories.FAST_FOOD, item)

        yield item
