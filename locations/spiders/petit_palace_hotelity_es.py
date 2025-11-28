from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class PetitPalaceHotelityESSpider(SitemapSpider, StructuredDataSpider):
    name = "petit_palace_hotelity_es"
    item_attributes = {"brand": "Petit Palace Hotelity", "brand_wikidata": "Q125472094"}
    sitemap_urls = ["https://www.petitpalace.com/sitemap.xml"]
    sitemap_rules = [(r"/es/[a-z-]+\/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace("Petit Palace ", "")
        apply_category(Categories.HOTEL, item)
        yield item
