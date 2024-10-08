import scrapy
from scrapy.selector import Selector

from locations.dict_parser import DictParser


class LeCrobagDESpider(scrapy.Spider):
    name = "le_crobag_de"
    item_attributes = {"brand": "Le Crobag", "brand_wikidata": "Q1558025"}

    def start_requests(self):
        yield scrapy.http.FormRequest(
            url="https://www.lecrobag.de/en/shops-en/locations.html",
            method="POST",
            formdata={
                "task": "search",
                "radius": "-1",
                "option": "com_mymaplocations",
                "limit": "0",
                "component": "com_mymaplocations",
                "itemid": "138",
                "zoom": "6",
                "format": "json",
                "limitstart": "0",
            },
            headers={
                "Accept": "application/json",
            },
        )

    def parse(self, response):
        for feature in response.json()["features"]:
            item = DictParser.parse(feature)

            item["website"] = response.urljoin(feature["properties"]["url"])
            item["lon"] = feature["geometry"]["coordinates"][0]
            item["lat"] = feature["geometry"]["coordinates"][1]

            description_elem = Selector(text=feature["properties"]["description"])
            item["phone"] = description_elem.xpath('//a[contains(@href, "tel")]/text()').extract_first()
            address_text = description_elem.xpath('//span[@class="locationaddress"]/text()').extract()
            item["street_address"] = "".join(address_text[:-2]).strip()
            item["postcode"] = address_text[-2].strip().split("\xa0")[0]
            item["city"] = address_text[-2].strip().split("\xa0")[1].rstrip(",")

            yield item
