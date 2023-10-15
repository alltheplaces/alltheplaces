from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BurgerKingPLSpider(Spider):
    name = "burger_king_pl"
    start_urls = ["https://burgerking.pl/restaurants"]
    item_attributes = {"brand": "Burger King", "brand_wikidata": "Q177054"}

    def parse(self, response, **kwargs):
        nextBuildId = response.xpath("//script[contains(@src, '_ssgManifest.js')]/@src").get().split("/")[3]
        url = f"https://burgerking.pl/_next/data/{nextBuildId}/restaurants.json"
        yield JsonRequest(url=url, callback=self.parse_api)

    def parse_api(self, response, **kwargs):
        for location in response.json()["pageProps"]["initialState"]["restaurant"]["restaurants"].values():
            if not location["active"] or location["tempDisabled"]:
                continue
            item = DictParser.parse(location)
            item["image"] = location["imgUrl"]
            item["lat"] = location["geoPosition"]["lat"]
            item["lon"] = location["geoPosition"]["lng"]
            openingHours = OpeningHours()
            for day, ranges in location["weeklyWorkingHours"].items():
                for r in ranges:
                    openingHours.add_ranges_from_string(f"{day} {r['from']}-{r['to']}")
            item["opening_hours"] = openingHours
            yield item
