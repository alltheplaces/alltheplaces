from scrapy import Spider

from locations.dict_parser import DictParser


class RobinsonsBreweryGBSpider(Spider):
    name = "robinsons_brewery_gb"
    item_attributes = {
        "brand": "Robinsons Brewery",
        "brand_wikidata": "Q7353116",
    }
    start_urls = ["https://www.robinsonsbrewery.com/page-data/search-results/page-data.json"]

    def parse(self, response, **kwargs):
        for location in response.json()["result"]["data"]["allWpPub"]["nodes"]:
            item = DictParser.parse(location["PubData"])
            item["ref"] = location["PubData"]["googlePlaceId"]
            item["city"] = location["PubData"]["displayLocation"]
            yield item
