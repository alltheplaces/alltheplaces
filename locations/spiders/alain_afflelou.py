import re

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
    sitemap_rules = [(r"afflelou\.[a-z]+/optic[a-z]+/.+/afflelou-", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        # ES/BE/MA names are "Óptica/Opticien ALAIN AFFLELOU <street address>", so only FR names give a branch
        if m := re.fullmatch(r"Opticien (.+) - ALAIN AFFLELOU", item.pop("name")):
            item["branch"] = m.group(1)
        apply_category(Categories.SHOP_OPTICIAN, item)
        yield item
