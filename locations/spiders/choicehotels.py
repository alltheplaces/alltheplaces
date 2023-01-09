import json
import re

from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class ChoiceHotelsSpider(SitemapSpider):
    name = "choicehotels"
    item_attributes = {"brand": "Choice Hotels", "brand_wikidata": "Q1075788"}
    allowed_domains = ["choicehotels.com"]
    sitemap_urls = ["https://www.choicehotels.com/propertysitemap.xml"]
    user_agent = BROWSER_DEFAULT
    download_delay = 5

    brand_mapping = {
        "AC": ("Ascend Hotel Collection", "Q113152464"),
        "BR": ("Cambria Hotels", "Q113152476"),
        "CI": ("Comfort Inn", "Q113152349"),
        "CL": ("Clarion Hotels", "Q113152454"),
        "CS": ("Comfort Suites", "Q55525150"),
        "EL": ("Econo Lodge", "Q5333330"),
        "MS": ("MainStay Suites", "Q113152432"),
        "QI": ("Quality Inn", "Q113152195"),
        "RW": ("Rodeway Inn", "Q7356709"),
        "SB": ("Suburban Extended Stay Hotel", "Q113152401"),
        "SL": ("Sleep Inn", "Q69588194"),
        "WS": ("WoodSpring Suites", "Q30672853"),
    }

    def parse(self, response):
        script = "".join(response.xpath("//script/text()").extract())
        data = json.loads(re.search(r"window.PRELOADED_STATE = (.*)?;", script).group(1))["page"]

        # Remove unused extra bits to get to the random key with the useful stuff in it
        data.pop("referrerState", None)
        data.pop("screenParams", None)
        data.pop("hasUserScrolled", None)
        data.pop("ready", None)
        data = list(data.values())[0]

        if "property" not in data:
            return

        properties = {
            "ref": data["property"]["id"],
            "name": data["property"]["name"],
            "street_address": data["property"]["address"]["line1"],
            "city": data["property"]["address"]["city"],
            "state": data["property"]["address"].get("subdivision"),
            "postcode": data["property"]["address"].get("postalCode"),
            "country": data["property"]["address"]["country"],
            "phone": data["property"]["phone"],
            "lat": data["property"]["lat"],
            "lon": data["property"]["lon"],
            "brand": data["property"]["brandName"],
            "website": response.url,
        }

        brand_info = self.brand_mapping.get(data["property"]["brandCode"])
        if brand_info:
            brand_name, brand_wikidata = brand_info
            properties["brand"] = brand_name
            properties["brand_wikidata"] = brand_wikidata
        else:
            self.logger.warning(
                "Missing brand mapping for %s, %s",
                data["property"]["brandCode"],
                data["property"]["brandName"],
            )

        yield Feature(**properties)
