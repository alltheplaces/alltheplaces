from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AldiSudITSpider(SitemapSpider, StructuredDataSpider):
    name = "aldi_sud_it"
    item_attributes = {"brand_wikidata": "Q41171672"}
    sitemap_urls = ["https://www.aldi.it/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.aldi\.it\/it\/trova-il-punto-vendita\/aldi-[-\w]+\/aldi-[-\w]+\.html$",
            "parse_sd",
        )
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("ALDI ")

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
