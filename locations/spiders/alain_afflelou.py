from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AlainAfflelouSpider(SitemapSpider, StructuredDataSpider):
    name = "alain_afflelou"
    item_attributes = {"brand": "Alain Afflelou", "brand_wikidata": "Q2829511"}
    sitemap_urls = [
        "https://www.afflelou.com/robots.txt",
        "https://www.afflelou.es/sitemap.xml",
        "https://www.afflelou.ma/robots.txt",
        "https://www.afflelou.be/robots.txt",
    ]
    sitemap_rules = [(r"afflelou\.[a-z]+/optic[a-z]+/", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("ALAIN AFFLELOU ")
        apply_category(Categories.SHOP_OPTICIAN, item)
        yield item
