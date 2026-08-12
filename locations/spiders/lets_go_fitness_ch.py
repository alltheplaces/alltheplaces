from typing import Any

from chompjs import chompjs
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class LetsGoFitnessCHSpider(Spider):
    name = "lets_go_fitness_ch"
    item_attributes = {"brand": "Let's Go Fitness", "brand_wikidata": "Q141005985"}
    start_urls = ["https://www.letsgofitness.ch/fr/clubs/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "allStrapiClub")]/text()').get()
        )["result"]["data"]["allStrapiClub"]["nodes"]:
            if location["locale"] != "fr":
                continue
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["lat"] = location["geolocation"]["latitude"]
            item["lon"] = location["geolocation"]["longitude"]
            item["ref"] = location["deeplink"].strip("/")
            item["website"] = "https://www.letsgofitness.ch/fr/club/{}/".format(item["ref"])
            apply_category(Categories.GYM, item)
            yield item
