from locations.spiders.cineworld_gb_je import CineworldGBJESpider
from locations.spiders.millies_gb import MilliesGBSpider
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class BaskinRobbinsGBIEJESpider(AgileStoreLocatorSpider):
    name = "baskin_robbins_gb_ie_je"
    item_attributes = {"brand": "Baskin-Robbins", "brand_wikidata": "Q584601"}
    allowed_domains = ["baskinrobbins.co.uk"]

    def parse_item(self, item, location):
        if "(Cineworld)" in item["name"]:
            item["located_in"] = CineworldGBJESpider.item_attributes["brand"]
            item["located_in_wikidata"] = CineworldGBJESpider.item_attributes["brand_wikidata"]
            item["name"] = item["name"].replace("(Cineworld)", "").strip()
        elif "(Millies Cookies)" in item["name"]:
            item["located_in"] = MilliesGBSpider.item_attributes["brand"]
            item["located_in_wikidata"] = MilliesGBSpider.item_attributes["brand_wikidata"]
            item["name"] = item["name"].replace("(Millies Cookies)", "").strip()
        yield item
