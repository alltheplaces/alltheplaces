from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SwissLifeFRSpider(SitemapSpider, StructuredDataSpider):
    name = "swiss_life_fr"
    item_attributes = {"brand": "Swiss Life", "brand_wikidata": "Q667350"}
    sitemap_urls = ["https://agences.swisslife.fr/sitemap_pois.xml"]
    sitemap_rules = [(r"", "parse")]
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.OFFICE_INSURANCE, item)
        item["branch"] = item.pop("name", "")
        yield item
