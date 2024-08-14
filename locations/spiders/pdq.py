import scrapy
import xmltodict

from locations.items import Feature


class PdqSpider(scrapy.Spider):
    name = "pdq"
    item_attributes = {"brand": "PDQ", "brand_wikidata": "Q87675367"}
    allowed_domains = ["eatpdq.qatserver.com"]
    start_urls = [
        "https://eatpdq.qatserver.com/Widgets/LocationSearchResult.ashx?latitude=32.9754859&longitude=-96.8853773&distance=6000"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for data in xmltodict.parse(response.text).get("markers").get("marker"):
            item = Feature()
            item["ref"] = data.get("@id")
            item["website"] = data.get("@href")
            item["name"] = data.get("@name")
            item["lat"] = data.get("@lat")
            item["lon"] = data.get("@lng")
            item["addr_full"] = data.get("@addressTEXT")
            item["street_address"] = data.get("@addressTEXT").split(", ")[0]
            item["city"] = data.get("@addressTEXT").split(", ")[1]
            item["state"] = data.get("@addressTEXT").split(", ")[2].split()[0]
            item["postcode"] = data.get("@addressTEXT").split(", ")[2].split()[-1]

            yield item
