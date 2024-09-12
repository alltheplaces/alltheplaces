from chompjs import parse_js_object
from scrapy import Selector, Spider

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

    def parse(self, response):
        data_raw = response.xpath('.//script[contains(text(), "window._gmData.infoWindows")]/text()').get()
        locations = parse_js_object(data_raw.split("['base-finder']")[1])

        for location in locations.values():
            selector = Selector(text=location["content"])
            item = Feature()
            item["name"] = selector.xpath("//h3/text()").get()
            item["ref"] = selector.xpath('//p/strong[contains(text(),"Station number:")]/../text()').get()
            item["phone"] = selector.xpath('//a[contains(@href, "tel:")]/@href').get()
            item["website"] = selector.xpath('//a[contains(@href, "nsri.org.za")]/@href').get()

            coordinates = selector.xpath('//p/strong[contains(text(),"Coordinates:")]/../text()').get().split(",")
            item["lat"] = coordinates[0]
            item["lon"] = coordinates[1]

            yield item
