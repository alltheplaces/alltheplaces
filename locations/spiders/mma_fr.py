from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class MmaFRSpider(SitemapSpider, StructuredDataSpider):
    name = "mma_fr"
    item_attributes = {
        "brand": "MMA",
        "brand_wikidata": "Q3331046",
    }
    sitemap_urls = ["https://agence.mma.fr/home.sitemap.xml"]
    sitemap_rules = [
        (r"", "parse_sd"),
    ]
    wanted_types = ["InsuranceAgency"]
    drop_attributes = ["facebook", "image"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.OFFICE_INSURANCE, item)
        item["branch"] = (item.pop("name", "") or "").removeprefix("AGENCE D'ASSURANCE MMA ")
        yield item
