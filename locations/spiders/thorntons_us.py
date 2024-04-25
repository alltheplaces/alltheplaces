from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature


class ThorntonsUSSpider(Spider):
    name = "thorntons_us"
    item_attributes = {"brand": "Thorntons", "brand_wikidata": "Q7796584"}
    start_urls = ["https://www.mythorntons.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@data-type="store"]'):
            item = Feature()
            item["ref"] = location.xpath('./p/span[@data-type="name"]/text()').get().split("#", 1)[1]
            item["street_address"] = location.xpath('./p/span[@data-type="address"]/text()').get()
            item["city"] = location.xpath('./p/span[@data-type="city"]/text()').get()
            item["state"] = location.xpath('./p/span[@data-type="state"]/text()').get()
            item["postcode"] = location.xpath('./p/span[@data-type="zip"]/text()').get()
            item["phone"] = location.xpath('./p/span[@data-type="phone"]/text()').get()

            tags = location.xpath("./p/@class").get().split(" ")
            apply_yes_no(Fuel.E85, item, "E85" in tags)
            apply_yes_no(Fuel.KEROSENE, item, "Kerosene" in tags)
            apply_yes_no(Fuel.E15, item, "Unleaded15" in tags)
            apply_yes_no(Extras.CAR_WASH, item, "carwash" in tags)
            apply_yes_no(Extras.SHOWERS, item, "shower" in tags)

            apply_category(Categories.FUEL_STATION, item)

            item["lat"] = float(location.xpath(".//@data-latitude").get())
            item["lon"] = float(location.xpath(".//@data-longitude").get())
            if item["lat"] < 0:  # :(
                item["lat"], item["lon"] = item["lon"], item["lat"]

            yield item
