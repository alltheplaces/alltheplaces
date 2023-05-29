import json
import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class ChoiceHotelsSpider(SitemapSpider):
    name = "choice_hotels"
    item_attributes = {"brand": "Choice Hotels", "brand_wikidata": "Q1075788"}
    allowed_domains = ["choicehotels.com"]
    sitemap_urls = ["https://www.choicehotels.com/propertysitemap.xml"]
    user_agent = BROWSER_DEFAULT
    download_delay = 5
    requires_proxy = True

    brand_mapping = {
        "AC": ("Ascend Hotel Collection", "Q113152464"),
        "BR": ("Cambria Hotel", "Q113152476"),
        "CI": ("Comfort Inn", "Q113152349", Categories.HOTEL),
        "CL": ("Clarion Hotels", "Q78165540"),
        "CS": ("Comfort Suites", "Q55525150"),
        "EL": ("Econo Lodge", "Q5333330"),
        "MS": ("MainStay Suites", "Q113152432"),
        "QI": ("Quality Inn", "Q113152195", Categories.HOTEL),
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

        if brand_info := self.brand_mapping.get(data["property"]["brandCode"]):
            properties["brand_wikidata"] = brand_info[1]
            if len(brand_info) == 3:
                apply_category(brand_info[2], properties)
        else:
            self.crawler.stats.inc_value(
                f'atp/choice_hotels/unmapped_category/{data["property"]["brandCode"]}/{data["property"]["brandName"]}'
            )
            self.crawler.stats.inc_value(f"atp/choice_hotels/unmapped_category/{response.url}")
            self.logger.warning(
                "Missing brand mapping for %s, %s", data["property"]["brandCode"], data["property"]["brandName"]
            )

        yield Feature(**properties)
