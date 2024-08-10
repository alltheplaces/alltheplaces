from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature


class NsriBasesZASpider(Spider):
    name = "nsri_bases_za"
    item_attributes = {
        "operator": "National Sea Rescue Institute",
        "operator_wikidata": "Q6978306",
        "extras": Categories.WATER_RESCUE.value,
    }
    start_urls = ["https://www.nsri.org.za/rescue/base-finder"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        script = [s for s in response.xpath("//script") if "window._gmData.infoWindows['base-finder']" in s.get()][0]
        locations = script.re(r".*\'[0-9]+-baseLocation\':\s\{\"content\":\"(.+)\"\},")

        for location in locations:
            selector = Selector(text=location.replace("\\/", "/").replace('\\"', '"'))
            item = Feature()
            item["name"] = selector.xpath("//h3/text()").get()
            item["ref"] = selector.xpath('//p/strong[contains(text(),"Station number:")]/../text()').get()
            item["phone"] = selector.xpath('//a[contains(@href, "tel:")]/text()').get()
            item["website"] = selector.xpath('//a[contains(@href, "nsri.org.za")]/@href').get()

            coordinates = selector.xpath('//p/strong[contains(text(),"Coordinates:")]/../text()').get().split(",")
            item["lat"] = coordinates[0]
            item["lon"] = coordinates[1]

            yield item
