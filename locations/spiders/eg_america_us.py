from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class EgAmericaUSSpider(Spider):
    name = "eg_america_us"
    allowed_domains = ["www.cumberlandfarms.com"]
    # The provided start_urls[0] returns all brand locations due to
    # high/non-existent page number resulting in all locations being
    # returned. The domain of start_urls[0] can be interchanged with
    # domains belonging to other brands of EG America.
    start_urls = ["https://www.cumberlandfarms.com/api/stores-locator/store-locator-search/results?pageNumber=10000"]
    brands = {
        1: {"brand": "Cumberland Farms", "brand_wikidata": "Q1143685"},
        11: {"brand": "Quik Stop", "brand_wikidata": "Q105141709"},
        12: {"brand": "TomThumb", "brand_wikidata": "Q123012206"},
        13: {"brand": "Turkey Hill", "brand_wikidata": "Q42376970"},
        # bannerid=14 is not used on any store locator for EG America
        # brands however street level imagery appears to show these
        # locations as Turkey Hill branded fuel stations.
        14: {"brand": "Turkey Hill", "brand_wikidata": "Q42376970"},
        15: {"brand": "Minit Mart", "brand_wikidata": "Q18154470"},
        16: {"brand": "Fastrac", "brand_wikidata": "Q117324848"},
        17: {"brand": "Certified Oil", "brand_wikidata": "Q100148356"},
        18: {"brand": "Kwik Shop", "brand_wikidata": "Q6450417"},
        19: {"brand": "Loaf 'N Jug", "brand_wikidata": "Q6663398"},
        20: {"brand": "Sprint", "brand_wikidata": "Q123012447"},
    }

    def start_requests(self):
        yield JsonRequest(url=self.start_urls[0], callback=self.parse)

    def parse(self, response):
        for location in response.json()["value"]["mapResults"]:
            item = DictParser.parse(location)
            item.update(self.brands[location["bannerId"]])
            item["street_address"] = item.pop("addr_full", None)
            item["website"] = location.get("pageUrl")
            apply_category(Categories.FUEL_STATION, item)
            yield item
