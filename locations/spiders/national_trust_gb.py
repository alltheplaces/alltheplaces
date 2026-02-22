from scrapy import Spider

from locations.categories import apply_category
from locations.dict_parser import DictParser


class NationalTrustGBSpider(Spider):
    name = "national_trust_gb"
    item_attributes = {"operator": "National Trust", "operator_wikidata": "Q333515", "nsi_id": "N/A"}
    allowed_domains = ["www.nationaltrust.org.uk"]
    start_urls = [
        "https://www.nationaltrust.org.uk/api/search/places?query=sw6%203er&placeSort=distance&lat=51.4672197&lon=-0.1925168&milesRadius=10000&pageStartIndex=0&pageSize=10000&lang=en&publicationChannel=NATIONAL_TRUST_ORG_UK&maxPlaceResults=1000&maxLocationPageResults=0"
    ]

    def parse(self, response):
        for data in response.json()["pagedMultiMatch"]["results"]:
            item = DictParser.parse(data)
            item["ref"] = data["id"]["value"]
            item["image"] = data["imageUrl"]

            apply_category({"tourism": "attraction"}, item)

            yield item
