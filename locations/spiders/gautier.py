from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class GautierSpider(SitemapSpider, StructuredDataSpider):
    name = "gautier"
    item_attributes = {"brand": "Gautier", "brand_wikidata": "Q5527930"}
    sitemap_urls = ["https://www.gautier-furniture.com/sitemap-gautier-furniture-com_fr_FR.xml"]
    sitemap_rules = [("/fr_FR/s/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace("Meubles ", "").replace("Gautier ", "")
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        item["image"] = None

        apply_category(Categories.SHOP_FURNITURE, item)

        yield item
