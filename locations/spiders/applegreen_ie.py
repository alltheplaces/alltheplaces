from urllib.parse import urljoin

from scrapy import Spider

from locations.categories import Access, Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class ApplegreenIESpider(Spider):
    name = "applegreen_ie"
    item_attributes = {"brand": "Applegreen", "brand_wikidata": "Q7178908"}
    start_urls = ["https://locations.applegreen.com/wp-json/locations/v1/search?distance=100"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address_1"], location["address_2"]])
            item["website"] = urljoin("https://locations.applegreen.com/locations", location["link"])
            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Extras.TOILETS, item, location["toilet"])
            apply_yes_no(Extras.CAR_WASH, item, location["car_wash"])
            apply_yes_no(Extras.ICE_CREAM, item, location["icecream"])
            apply_yes_no(Access.HGV, item, location["hgv"])
            yield item
