from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class IxinaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "ixina_fr"
    item_attributes = {"brand": "Ixina", "brand_wikidata": "Q3156424"}
    sitemap_urls = ["https://www.ixina.fr/pages/sitemap.xml"]
    sitemap_rules = [
        (r"/trouvez-votre-magasin/magasin-de.*", "parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Magasin ixina ", "")
        yield item
