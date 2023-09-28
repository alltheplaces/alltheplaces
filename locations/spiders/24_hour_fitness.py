import scrapy

from locations.dict_parser import DictParser


class TwentyFourHourFitnessSpider(scrapy.Spider):
    name = "24_hour_fitness"
    item_attributes = {"brand_wikidata": "Q4631849"}
    start_urls = ["https://www.24hourfitness.com/Website/ClubLocation/OpenClubs/"]

    def parse(self, response):
        for club in response.json()["clubs"]:
            club["ref"] = club["clubNumber"]
            club["address"]["street_address"] = club["address"].pop("street")
            club["website"] = "https://www.24hourfitness.com/Website/Club/" + club["clubNumber"]
            club["location"] = club.pop("coordinate")
            item = DictParser.parse(club)
            if club["type"] == "SuperSport":
                item["brand"] = "24 Hour Fitness Super Sport"
            elif club["type"] == "Sport":
                item["brand"] = "24 Hour Fitness Sport"
            elif club["type"] == "Active":
                item["brand"] = "24 Hour Fitness"
            else:
                item["extras"] = {"type": club["type"]}
            yield item
