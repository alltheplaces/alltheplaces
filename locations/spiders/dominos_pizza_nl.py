from urllib.parse import urljoin

import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaNLSpider(scrapy.Spider):
    name = "dominos_pizza_nl"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def start_requests(self):
        for city in city_locations("NL", 18000):
            yield JsonRequest(
                url=f"https://www.dominos.nl/dynamicstoresearchapi/getstoresfromquery?lon={city['longitude']}&lat={city['latitude']}",
            )

    def parse(self, response, **kwargs):
        for store in response.json()["PickupSearchStore"]:
            store.update(store["locations"].pop(0))
            store.update(store.pop("address"))
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["website"] = urljoin("https://www.dominos.nl", store["properties"]["storeUrl"])
            for details in store["attributes"]:
                if details["key"] == "streetName":
                    item["street_address"] = details["value"]
                elif details["key"] == "postCode":
                    item["postcode"] = details["value"]
            yield item

    # def parse_store(self, response: Response) -> Any:
    #     address_data = response.xpath('//a[@id="open-map-address"]/text()').getall()
    #     locality_data = re.search(r"(.*) ([A-Z]{2}) (.*)", address_data[1].strip())
    #     properties = {
    #         "ref": re.match(self.url_regex, response.url).group(1),
    #         "branch": response.xpath('//*[@class="storetitle"]/text()').get("").removeprefix("Domino's Pizza "),
    #         "street_address": address_data[0].strip().strip(","),
    #         "lat": response.xpath('//input[@id="store-lat"]/@value').get().replace(",", "."),
    #         "lon": response.xpath('//input[@id="store-lon"]/@value').get().replace(",", "."),
    #         "phone": response.xpath('//a[contains(@href, "tel:")]/@href').get(),
    #         "website": response.url,
    #     }
    #     if locality_data:
    #         properties["city"] = locality_data.group(1)
    #         properties["postcode"] = locality_data.group(3)
    #     yield Feature(**properties)
