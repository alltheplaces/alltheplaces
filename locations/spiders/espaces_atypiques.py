from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider, clean_facebook


class EspacesAtypiquesSpider(SitemapSpider, StructuredDataSpider):
    name = "espaces_atypiques"
    item_attributes = {
        "brand": "Espaces Atypiques",
        "brand_wikidata": "Q139386727",
    }
    sitemap_urls = ["https://www.espaces-atypiques.com/agence-sitemap.xml"]
    sitemap_rules = [
        (r".com/(?!en/)", "parse"),
    ]
    wanted_types = ["RealEstateAgent"]
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name", "").removeprefix("Espaces Atypiques ")
        if clean_facebook(item.get("facebook")) == "https://www.facebook.com/espaces.atypiques":
            item.pop("facebook")
        apply_category(Categories.OFFICE_ESTATE_AGENT, item)
        yield item
