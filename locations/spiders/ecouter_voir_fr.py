from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider, clean_facebook


class EcouterVoirFrSpider(SitemapSpider, StructuredDataSpider):
    name = "ecouter_voir_fr"
    item_attributes = {
        "brand": "Écouter Voir",
        "brand_wikidata": "Q18414551",
    }
    sitemap_urls = ["https://magasins.ecoutervoir.fr/sitemap.xml"]
    sitemap_rules = [(r"[0-9]+$", "parse_sd")]
    drop_attributes = ["image"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        name = item.pop("name", "")
        if "audition" in name.lower():
            apply_category(Categories.SHOP_HEARING_AIDS, item)
        else:
            apply_category(Categories.SHOP_OPTICIAN, item)

        if clean_facebook(item.get("facebook")) == "https://www.facebook.com/ecoutervoir.officiel/":
            item["facebook"] = None

        yield item
