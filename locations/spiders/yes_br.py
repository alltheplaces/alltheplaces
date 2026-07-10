from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class YesBRSpider(SitemapSpider, StructuredDataSpider):
    name = "yes_br"
    item_attributes = {"brand": "Yes! Idiomas", "brand_wikidata": "Q121365811"}
    sitemap_urls = ["https://www.yes.com.br/sitemap.xml"]
    sitemap_rules = [(r"/escolas/[^/]+$", "parse")]
    wanted_types = ["LanguageSchool"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("YES! ", "").title()
        item["website"] = response.url
        apply_category(Categories.LANGUAGE_SCHOOL, item)
        yield item
