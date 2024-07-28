from typing import Any, Iterable

from scrapy import FormRequest, Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature


class SpeedwayUSSpider(Spider):
    name = "speedway_us"
    item_attributes = {"brand": "Speedway", "brand_wikidata": "Q7575683"}
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def make_request(self, offset: int) -> FormRequest:
        return FormRequest(
            url="https://www.speedway.com/locations/search",
            formdata={
                "StartIndex": str(offset),
                "Limit": "1000",
                "Latitude": "0",
                "Longitude": "0",
                "Radius": "20000",
            },
            meta={"offset": offset},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//section[@class="c-location-card"]'):
            item = Feature()
            item["ref"] = location.xpath("@data-costcenter").get()
            item["lat"] = location.xpath("@data-latitude").get()
            item["lon"] = location.xpath("@data-longitude").get()
            item["state"] = location.xpath("@data-state").get()
            item["website"] = response.urljoin(location.xpath(".//a/@href").get())
            item["addr_full"] = location.xpath(".//@data-location-address").get()
            item["street_address"] = location.xpath('.//h2[@data-location-info-window-data="address"]/text()').get()
            item["phone"] = location.xpath('.//li[data-location-details="phone"]/text()').get()

            amenities = location.xpath(
                './/div[@class="c-location-options--amenities"]/ul[@class="c-location-options__list"]/li/span/text()'
            ).getall()
            fuels = location.xpath(
                './/div[@class="c-location-options--fuel"]/ul[@class="c-location-options__list"]/li/span/text()'
            ).getall()

            if "Open 24 Hours" in amenities:
                item["opening_hours"] = "24/7"

            # TODO: "Money Orders" "Propane Exchange"
            apply_yes_no(Extras.ATM, item, "ATM" in amenities)
            apply_yes_no(Extras.CAR_WASH, item, "Car Wash" in amenities)
            apply_yes_no(Fuel.PROPANE, item, "Propane Exchange" in amenities)
            # TODO: DEF Plus Premium Unleaded
            apply_yes_no(Fuel.DIESEL, item, "Auto Diesel" in fuels)
            apply_yes_no(Fuel.E85, item, "E-85" in fuels)
            apply_yes_no(Fuel.E15, item, "E15" in fuels)
            apply_yes_no(Fuel.E20, item, "E20" in fuels)
            apply_yes_no(Fuel.E30, item, "E30" in fuels)
            apply_yes_no(Fuel.ETHANOL_FREE, item, "Ethanol Free" in fuels)
            apply_yes_no(Fuel.KEROSENE, item, "Kerosene" in fuels)
            apply_yes_no(Fuel.OCTANE_90, item, "Plus 90" in fuels)
            apply_yes_no(Fuel.OCTANE_91, item, "Plus 91" in fuels)

            apply_category(Categories.FUEL_STATION, item)

            yield item

        if response.meta["offset"] < int(response.xpath('//input[@id="totalsearchresults"]/@value').get()):
            yield self.make_request(response.meta["offset"] + 1000)
