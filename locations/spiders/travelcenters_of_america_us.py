from scrapy import Spider
from scrapy.http import FormRequest

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class TravelCentersOfAmericaUSSpider(Spider):
    name = "travelcenters_of_america_us"
    item_attributes = {"brand": "TravelCenters of America", "brand_wikidata": "Q7835892"}
    allowed_domains = ["www.ta-petro.com"]
    start_urls = ["https://www.ta-petro.com/api/locations/search"]

    def start_requests(self):
        data = {"PostalCode": "", "StateCode": "", "HighwayId": "0"}
        for url in self.start_urls:
            yield FormRequest(url=url, method="POST", formdata=data, headers={"Accept": "application/json"})

    # Note: the response from the API is extremely slow to arrive.
    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            match location["BrandId"]:
                case 1:
                    item["brand"] = "TA"
                case 2:
                    item["brand"] = "Petro"
                case 3:
                    item["brand"] = "TA Express"
            item["ref"] = location["TAAccessNumber"]
            item["street_address"] = item.pop("street")
            item["website"] = (
                "https://www.ta-petro.com/location/" + item["state"].lower() + "/" + location["FileName"] + "/"
            )
            fuel_codes = [fuel_price["FuelCode"] for fuel_price in location["FuelPrices"]]
            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Fuel.OCTANE_87, item, 1 in fuel_codes, False)
            apply_yes_no(Fuel.OCTANE_89, item, 2 in fuel_codes, False)
            apply_yes_no(Fuel.OCTANE_93, item, 3 in fuel_codes, False)
            apply_yes_no(Fuel.DIESEL, item, 20 in fuel_codes, False)
            apply_yes_no(Fuel.ADBLUE, item, 143 in fuel_codes, False)
            yield item
