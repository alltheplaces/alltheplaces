from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.items import Feature

# from locations.categories import Categories
# from locations.hours import DAYS_EN, OpeningHours

# https://www.lighthouse.gr/
#
# Detected by:
# meta name="generator" content="Created by Lighthouse, powered by VENDD e-commerce platform - www.lighthouse.gr"
# data-control="box"


class LighthouseSpider(Spider):
    def parse(self, response, **kwargs):
        for location in response.xpath("//article[@data-control='box']"):
            item = Feature()
            item["ref"] = location.xpath("@id").get()
            item["lat"] = location.xpath("@data-latitude").get()
            item["lon"] = location.xpath("@data-longitude").get()
            item["name"] = location.xpath("*[contains(@class, 'name-container')]/span/text()").get()
            item["street_address"] = location.xpath(
                "*[contains(@class, 'info-container')]/*[contains(@class, 'address-one')]/text()"
            ).get()
            phones = location.xpath("*[contains(@class, 'info-container')]/*[contains(@class, 'phone')]/text()").get()
            if phones is not None:
                item["phone"] = phones.split(",")[0]

            for extra_feature in location.xpath("div[contains(@class, 'extra-features-container')]/ul/li"):
                self.map_extras(item, extra_feature, location)

            yield from self.parse_item(item, location) or []

    # Example:
    #         <div class="extra-features-container">
    #             <ul>
    #                   <li class="carwash" title="Car Wash"></li>
    #                   <li class="ekosmile" title="Ekosmile"></li>
    #                   <li class="supermarket" title="Supermarket"></li>
    #                   <li class="minimarket" title="Mini Market"></li>
    #             </ul>
    def map_extras(self, item, extra_feature, location):
        if extra_feature.xpath("@class").get() == "carwash":
            apply_yes_no(Extras.CAR_WASH, item, "car_wash", True)

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item
