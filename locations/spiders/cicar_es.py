from typing import Any

from scrapy.http import HtmlResponse, Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import StructuredDataSpider


class CicarESSpider(CrawlSpider, StructuredDataSpider):
    name = "cicar_es"
    item_attributes = {"brand": "CICAR", "brand_wikidata": "Q126181047"}
    start_urls = ["https://www.cicar.com/EN/canary-islands"]
    rules = [
        Rule(LinkExtractor(allow="/officeView/"), callback="parse_sd"),
    ]

    # Convert start url's response to HtmlResponse to make crawling possible
    def _parse(self, response: Response, **kwargs: Any) -> Any:
        return self._parse_response(
            response=HtmlResponse(url=response.url, body=response.text, encoding="utf-8"),
            callback=self.parse_start_url,
            cb_kwargs=kwargs,
            follow=True,
        )

    def pre_process_data(self, ld_data, **kwargs):
        for index, rule in enumerate(ld_data["openingHours"]):
            ld_data["openingHours"][index] = rule.replace("day:", "day ").replace("/", ",")

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["addr_full"] = clean_address(item.pop("street_address").replace("<br>", ", "))
        item["branch"] = item.pop("name").removeprefix("CICAR offices ")
        item.pop("email")
        extract_google_position(item, response)
        apply_category(Categories.CAR_RENTAL, item)
        yield item
