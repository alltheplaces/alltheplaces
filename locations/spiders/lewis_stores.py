import scrapy

from locations.dict_parser import DictParser


class LewisStoresSpider(scrapy.Spider):
    name = "lewis_stores"
    item_attributes = {"brand": "Lewis Stores", "brand_wikidata": "Q116474928"}

    def start_requests(self):
        yield scrapy.http.FormRequest(
            url="https://lewisstores.co.za/controllers/get_locations.php",
            formdata={"param1": "Lewis Stores"},
        )

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            country_code_mapping = {
                182: "NA",
                73: "ZA",
                219: "SZ",
                155: "LS",
                101: "BW",
            }
            item["name"] = location["StoreLocatorName"]
            item["email"] = item["email"].replace("NULL", "")
            item["country"] = country_code_mapping[location["CountryId"]]
            yield item
