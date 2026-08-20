from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CityaSpider(SitemapSpider, StructuredDataSpider):
    name = "citya"
    item_attributes = {
        "brand": "Citya",
        "brand_wikidata": "Q2974597",
    }
    sitemap_urls = ["https://www.citya.com/sitemap.agences.xml"]
    sitemap_rules = [(r"/agences-immobilieres/.*/[0-9]*$", "parse_sd")]

    drop_attributes = {"image", "twitter", "facebook"}

    def post_process_item(self, item, response, ld_data, **kwargs):

        if item["email"] in ["qualite@citya.com", "rgpd@citya.com"]:
            item.pop("email", None)

        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
