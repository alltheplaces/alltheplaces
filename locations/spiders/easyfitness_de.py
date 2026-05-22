import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EasyfitnessDESpider(SitemapSpider, StructuredDataSpider):
    name = "easyfitness_de"
    item_attributes = {"brand": "EasyFitness", "brand_wikidata": "Q106166703"}
    sitemap_urls = ["https://easyfitness.club/robots.txt"]
    sitemap_rules = [
        (r"/studio/([^/]+)/?$", "parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # To prevent one location from AE
        if item.get("country") == "AE":
            return

        item["ref"] = response.url.rstrip("/").split("/")[-1]

        if email_href := response.xpath('//a[contains(@href, "mailto:")]/@href').get():
            item["email"] = re.search(r"mailto:\s*([\w\.-]+@[\w\.-]+\.\w+)", email_href).group(1).strip()

        item["image"] = None

        yield item
