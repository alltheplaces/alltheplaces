from copy import deepcopy

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
        set_operator(CENTRAL_COOP, item)
        name = item["name"]
        if item.get("twitter") == "mycoopfood":
            item.pop("twitter", None)
        if item.get("facebook") == 'https://www.facebook.com/centralcoopfood"':
            item.pop("facebook", None)
        item.pop("image", None)
        item["website"] = response.url
        if "CLOSED" in name.upper():
            return
        if "FUNERAL" in name.upper() or "CREMATORIUM" in name.upper() or "COFFINS" in name.upper():
            apply_category(Categories.SHOP_FUNERAL_DIRECTORS, item)
            if "Central Co-op Funeral" in item["name"]:
                item.update(COOP_FUNERALCARE)
                item["branch"] = item.pop("name").replace("Central Co-op Funeral", "").strip(" -")
        elif "FLORIST" in name.upper():
            # No structured data on florist pages yet
            apply_category(Categories.SHOP_FLORIST, item)
            if "Central Co-op Florist" in item["name"]:
                item.update(CENTRAL_COOP)
                item["name"], item["branch"] = item["name"].split(" - ")
        else:
            if "PETROL" in name.upper():
                fuel_item = deepcopy(item)
                apply_category(Categories.FUEL_STATION, fuel_item)
                yield fuel_item
            apply_category(Categories.SHOP_CONVENIENCE, item)
            if item["name"].startswith("The Co-operative"):
                item.update(COOP_FOOD)
                item["branch"] = item["name"].replace("The Co-operative ", "")
            else:
                item.update(CENTRAL_COOP)
                item["name"], item["branch"] = item["name"].split(" - ")
        yield item
