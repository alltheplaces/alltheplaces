from typing import Any

from scrapy import Spider, Selector
from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.settings import ITEM_PIPELINES

class NsriBuoysZa(Spider):
    name = "nsri_buoys_za"
    item_attributes = {"operator": "National Sea Rescue Institute", "operator_wikidata": "Q6978306", "extras": Categories.RESCUE_BUOY.value}
    start_urls = ["https://www.nsri.org.za/water-safety/pink-rescue-buoys"]

    # custom_settings = {
    #    "ITEM_PIPELINES": ITEM_PIPELINES | {"locations.pipelines.apply_nsi_categories.ApplyNSICategoriesPipeline": None}
    # }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        script = [s for s in response.xpath('//script') if "window._gmData.infoWindows['buoy-finder']" in s.get()][0]
        locations = script.re(r".*\'[0-9]+-buoyLocation\':\s\{\"content\":\"(.+)\"\},")

        for location in locations:
            selector = Selector(text=location.replace("\\/", "/"))
            item = Feature()
            item["ref"] = selector.xpath("//h3/text()").get().removeprefix("-").strip()

            coordinates = selector.xpath("//p/text()").get().split(",")
            item["lat"] = coordinates[0]
            item["lon"] = coordinates[1]

            yield item