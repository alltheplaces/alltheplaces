from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class NationalTrustGBSpider(Spider):
    name = "national_trust_gb"
    item_attributes = {"brand": "National Trust", "brand_wikidata": "Q333515"}
    allowed_domains = ["www.nationaltrust.org.uk"]
    start_urls = [
        "https://www.nationaltrust.org.uk/api/search/places?query=sw6%203er&placeSort=distance&lat=51.4672197&lon=-0.1925168&milesRadius=10000&pageStartIndex=0&pageSize=10000&lang=en&publicationChannel=NATIONAL_TRUST_ORG_UK&maxPlaceResults=1000&maxLocationPageResults=0"
    ]

    def parse(self, response):
        for data in response.json()["pagedMultiMatch"]["results"]:
            item = DictParser.parse(data)
            item["ref"] = data["id"]["value"]
            item["image"] = data["imageUrl"]
            item["opening_hours"] = OpeningHours()
            yield item
