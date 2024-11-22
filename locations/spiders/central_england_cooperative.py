from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


def set_operator(brand: dict, item: Feature):
    item["operator"] = brand["brand"]
    item["operator_wikidata"] = brand["brand_wikidata"]


COOP_FOOD = {"brand": "The Co-operative Food", "brand_wikidata": "Q107617274"}
COOP_FUNERALCARE = {"brand": "The Co-operative Funeralcare", "brand_wikidata": "Q7726521"}

CENTRAL_COOP = {"brand": "Central England Co-operative", "brand_wikidata": "Q16986583"}


class CentralEnglandCooperativeSpider(SitemapSpider, StructuredDataSpider):
    name = "central_england_cooperative"
    sitemap_urls = ["https://stores.centralengland.coop/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/stores\.centralengland\.coop\/[-\w]+\/.*$", "parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["image"] = None
        set_operator(CENTRAL_COOP, item)
        name = item["name"]
        if "FOOD" in name.upper():
            apply_category(Categories.SHOP_CONVENIENCE, item)
            item.update(COOP_FOOD)
            item["branch"] = item.pop("name").split(" - ", 1)[1].strip()
        else:
            apply_category(Categories.SHOP_FUNERAL_DIRECTORS, item)
            if "Central Co-op Funeral" in item["name"]:
                item.update(COOP_FUNERALCARE)
                item["branch"] = item.pop("name").replace("Central Co-op Funeral", "").strip(" -")
        yield item
