from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MontessoriSchoolSpider(SitemapSpider, StructuredDataSpider):
    name = "montessori_school"
    item_attributes = {"brand": "Montessori School"}
    sitemap_urls = ["https://www.montessori.com/sitemaps/www-montessori-com-schools.xml"]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Any:
        item.pop("phone", None)
        item.pop("facebook", None)
        item["website"] = response.url
        apply_category(Categories.SCHOOL, item)
        yield item
