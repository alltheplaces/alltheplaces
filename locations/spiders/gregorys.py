import json

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class GregorysSpider(CamoufoxSpider):
    name = "gregorys"
    item_attributes = {"brand": "Γρηγόρης", "brand_wikidata": "Q62273834"}
    start_urls = ["https://corporate.gregorys.gr/en/xartis-katastimaton"]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response, **kwargs):
        for result in response.xpath("//*[@data-map-marker]"):
            data = json.loads(result.xpath("@data-map-marker").get())

            item = Feature()
            item["lat"] = data["Latitude"]
            item["lon"] = data["Longitude"]
            item["ref"] = result.xpath("./@data-id").get()
            item["addr_full"] = merge_address_lines([data["Title"], data["Address"]])

            if data["IsForeign"] is False:
                item["country"] = "GR"
            apply_category(Categories.FAST_FOOD, item)
            yield item
