from locations.storefinders.nomnom import NomNomSpider, slugify
from locations.user_agents import BROWSER_DEFAULT


class PandaExpressSpider(NomNomSpider):
    name = "panda_express"
    item_attributes = {"brand": "Panda Express", "brand_wikidata": "Q1358690"}
    start_urls = ["https://nomnom-prod-api.pandaexpress.com/extras/restaurant/summary/state"]
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item, response, feature):
        item["extras"]["website:menu"] = feature["url"]
        item["website"] = (
            f"https://www.pandaexpress.com/locations/{slugify(feature['state'])}/{slugify(feature['city'])}/{feature['extref']}"
        )
        yield item
