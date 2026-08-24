from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider, clean_facebook
from locations.categories import Categories, apply_category


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
        apply_category(Categories.SHOP_OPTICIAN, item)
        item.pop("name","")

        if(clean_facebook(item.get("facebook")) == "https://www.facebook.com/ecoutervoir.officiel/"):
            item["facebook"] = None

        yield item
