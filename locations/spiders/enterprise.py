import geonamescache
from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class EnterpriseSpider(Spider):
    name = "enterprise"
    item_attributes = {"brand": "Enterprise", "brand_wikidata": "Q17085454"}
    allowed_domains = ["prd.location.enterprise.com", "int1.location.enterprise.com"]

    def start_requests(self):
        gc = geonamescache.GeonamesCache()
        countries = gc.get_countries()
        for country_code in countries.keys():
            # It appears that countries are sharded between two
            # servers. Other servers are int2, xqa1, xqa2, xqa3
            # but search of these servers reveals no additional
            # locations on top of just prd and int1.
            for subdomain in ["prd", "int1"]:
                yield JsonRequest(
                    url=f"https://{subdomain}.location.enterprise.com/enterprise-sls/search/location/enterprise/web/country/{country_code}"
                )

    def parse(self, response):
        for location in response.json():
            if location["closed"] or not location["physicalLocation"]:
                continue
            item = DictParser.parse(location)
            item["ref"] = location["stationId"]
            item["name"] = location["locationNameTranslation"]
            item["street_address"] = clean_address(location["addressLines"])
            item["phone"] = location["formattedPhone"]
            apply_category(Categories.CAR_RENTAL, item)
            yield item
