import geonamescache
from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class EnterpriseSpider(Spider):
    name = "enterprise"
    item_attributes = {"brand": "Enterprise Rent-A-Car", "brand_wikidata": "Q17085454"}
    allowed_domains = ["prd.location.enterprise.com"]

    def start_requests(self):
        gc = geonamescache.GeonamesCache()
        countries = gc.get_countries()
        for country_code in countries.keys():
            yield JsonRequest(
                url=f"https://prd.location.enterprise.com/enterprise-sls/search/location/enterprise/web/country/{country_code}"
            )

    def parse(self, response):
        for location in response.json():
            if location["closed"] or not location["physicalLocation"]:
                continue
            item = DictParser.parse(location)
            item["ref"] = location["stationId"]
            item["name"] = location["locationNameTranslation"]
            item["street_address"] = ", ".join(filter(None, location["addressLines"]))
            item["phone"] = location["formattedPhone"]
            yield item
