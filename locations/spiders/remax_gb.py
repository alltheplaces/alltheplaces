import scrapy

from locations.dict_parser import DictParser


class RemaxGBSpider(scrapy.Spider):
    name = "remax_gb"
    item_attributes = {
        "brand": "RE/MAX",
        "brand_wikidata": "Q965845",
    }
    allowed_domains = ["remax.uk"]

    def start_requests(self):
        template = "https://remax.uk/api/locations?name={}"
        for i in range(97, 123):
            yield scrapy.Request(url=template.format(chr(i)), callback=self.parse_place_id)

    def parse_place_id(self, response):
        template = "https://remax.uk/api/locationsbyplaceid?placeid={}"
        for id in response.json().get("predictions"):
            yield scrapy.Request(url=template.format(id.get("place_id")), callback=self.parse)

    def parse(self, response):
        for data in response.json().get("branches"):
            item = DictParser.parse(data)
            item["ref"] = data.get("branch_id")
            item["name"] = data.get("branch_name")
            item["street_address"] = data.get("branch_address1")
            item["city"] = data.get("branch_town")
            item["postcode"] = data.get("branch_postcode")
            item["phone"] = data.get("branch_phone")
            item["email"] = data.get("branch_email")

            yield item
