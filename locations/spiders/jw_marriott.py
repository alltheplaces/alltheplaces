import json

import scrapy

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class JWMarriottSpider(scrapy.Spider):
    name = "jw_marriott"
    item_attributes = {
        "brand": "JW Marriott",
        "brand_wikidata": "Q1067636",
    }
    start_urls = ["https://pacsys.marriott.com/data/marriott_properties_JW_en-US.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response):
        data_js = json.loads(response.text)
        for region in data_js.get("regions"):
            for country in region.get("region_countries"):
                for state in country.get("country_states"):
                    for city in state.get("state_cities"):
                        for hotel in city.get("city_properties"):
                            item = DictParser.parse(hotel)
                            item["ref"] = hotel.get("marsha_code")
                            item["name"] = "JW Marriott"
                            item["country"] = country.get("country_code")
                            item["state"] = state.get("state_name")
                            item["image"] = hotel.get("exterior_photo")
                            item["extras"]["capacity:rooms"] = hotel.get("number_of_rooms")
                            item["extras"]["fax"] = hotel.get("fax")
                            if hotel.get("bookable"):
                                item["extras"]["reservation"] = "yes"
                            item["extras"]["description"] = hotel.get("description_main")
                            if hotel.get("has_sauna"):
                                item["extras"]["sauna"] = "yes"
                            # TODO: Does have "has_fitness", "has_golf", "reservation_phone"

                            yield item
