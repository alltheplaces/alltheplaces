from typing import Iterable

from scrapy.http import Response, TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MrowkaPLSpider(SitemapSpider, StructuredDataSpider):
    name = "mrowka_pl"
    item_attributes = {"brand": "PSB Mrówka", "brand_wikidata": "Q11786409"}
    sitemap_urls = ["https://mrowka.com.pl/sitemap.xml?Index=ShopStore"]
    sitemap_rules = [("/sklep-psb-mrowka/psb-mrowka-", "parse")]
    wanted_types = ["Store"]

    def _get_sitemap_body(self, response: Response) -> bytes | None:
        return response.body

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = None
        item["branch"] = response.xpath("//h1/text()").get().removeprefix("PSB Mrówka ")
        item["phone"] = response.xpath("//a[starts-with(@href, 'tel:')]/@href").get("").removeprefix("tel:")
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
