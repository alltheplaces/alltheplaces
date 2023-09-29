from urllib.parse import urljoin

from scrapy.spiders import Spider

from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address


class GigglingSquidGBSpider(Spider):
    name = "giggling_squid_gb"
    item_attributes = {"brand": "Giggling Squid", "brand_wikidata": "Q113127471"}
    start_urls = ["https://wp.gigglingsquid.com/wp-json/gs/v1/locations"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for location in response.json()["locations"]:
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["coordinates"]["lat"]
            item["lon"] = location["coordinates"]["long"]
            item["branch"] = location["name"]
            item["image"] = urljoin("https://www.gigglingsquid.com/", location["listImage"])
            item["addr_full"] = clean_address(location["address"])
            item["phone"] = location["phone"]
            item["website"] = urljoin("https://www.gigglingsquid.com/restaurant/", location["slug"])

            yield item
