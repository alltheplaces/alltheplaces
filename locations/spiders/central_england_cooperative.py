from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


def set_operator(brand: dict, item: Feature):
    item["extras"]["operator"] = brand["brand"]
    item["extras"]["operator:wikidata"] = brand["brand_wikidata"]


COOP_FOOD = {"brand": "The Co-operative Food", "brand_wikidata": "Q107617274"}
COOP_FUNERALCARE = {"brand": "The Co-operative Funeralcare", "brand_wikidata": "Q7726521"}

CENTRAL_COOP = {"brand": "Central England Co-operative", "brand_wikidata": "Q16986583"}


class CentralEnglandCooperativeSpider(SitemapSpider, StructuredDataSpider):
    name = "central_england_cooperative"
    sitemap_urls = ["https://stores.centralengland.coop/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/stores\.centralengland\.coop\/[-\w]+\/.*$", "parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["image"] = None

        if "logo-food" in ld_data["logo"]:
            apply_category(Categories.SHOP_CONVENIENCE, item)
            set_operator(CENTRAL_COOP, item)

            item.update(COOP_FOOD)
            item["brand"], item["branch"] = item.pop("name").split(" - ", 1)
        elif "logo-funeral" in ld_data["logo"]:
            apply_category(Categories.SHOP_FUNERAL_DIRECTORS, item)
            set_operator(CENTRAL_COOP, item)

            if "Central Co-op Funeral" in item["name"]:
                item.update(COOP_FUNERALCARE)
                item["branch"] = item.pop("name").replace("Central Co-op Funeral", "").strip(" -")
        else:
            apply_category(Categories.SHOP_FLORIST, item)
            set_operator(CENTRAL_COOP, item)

            item["brand"], item["branch"] = item.pop("name").split(" - ", 1)

        yield item
