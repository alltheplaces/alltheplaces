import json
import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import CHROME_LATEST


class ChoiceHotelsSpider(SitemapSpider):
    name = "choice_hotels"
    item_attributes = {"brand": "Choice Hotels", "brand_wikidata": "Q1075788"}
    allowed_domains = ["choicehotels.com"]
    # Sitemapindex with below in it is "https://www.choicehotels.com/sitemapindex.xml"
    sitemap_urls = ["https://www.choicehotels.com/brandsearchsitemap.xml.gz"]
    user_agent = CHROME_LATEST
    download_delay = 5  # Requested by https://www.choicehotels.com/robots.txt
    requires_proxy = True

    brand_mapping = {
        "AC": ("Ascend Hotel Collection", "Q113152464"),
        "BR": ("Cambria Hotel", "Q113152476"),
        "CC": ("Circus Circus", "", Categories.HOTEL),
        "CI": ("Comfort Inn", "Q113152349", Categories.HOTEL),
        "CL": ("Clarion Hotels", "Q10454567"),
        "CS": ("Comfort Suites", "Q55525150"),
        "CX": ("Country", "", Categories.HOTEL),
        "EC": ("El Cid", "", Categories.HOTEL),
        "EL": ("Econo Lodge", "Q5333330"),
        "EV": ("Everhome", "", Categories.HOTEL),
        "FR": ("RocketFuel", "", Categories.HOTEL),
        "MS": ("MainStay Suites", "Q113152432"),
        "PK": ("Park Plaza", "Q2052550"),
        "PD": ("Park Inn", "Q60711675"),
        "PN": ("Penn", "", Categories.HOTEL),
        "QI": ("Quality Inn", "Q113152195", Categories.HOTEL),
        "RB": ("Radisson Blu", "Q7281341"),
        "RR": ("Radisson RED", "Q28233721"),
        "RD": ("Radisson", "Q1751979"),
        "RV": ("Radisson Individuals", "", Categories.HOTEL),
        "RW": ("Rodeway Inn", "Q7356709"),
        "SB": ("Suburban Extended Stay Hotel", "Q113152401"),
        "SL": ("Sleep Inn", "Q69588194"),
        "WS": ("WoodSpring Suites", "Q30672853"),
    }

    def parse(self, response):
        if "notavail" in response.url:
            return
        data = json.loads(re.search(r"window.PRELOADED_STATE = (.*)?;", response.text).group(1))
        if hotels := DictParser.get_nested_key(data, "hotels"):
            for location in hotels:
                item = DictParser.parse(location)

                item["brand"] = location["brandName"]
                item["state"] = location["address"].get("subdivision")
                item["website"] = response.url

                if brand_info := self.brand_mapping.get(location["brandCode"]):
                    item["brand_wikidata"] = brand_info[1]
                    if len(brand_info) == 3:
                        apply_category(brand_info[2], item)
                else:
                    self.crawler.stats.inc_value(
                        f'atp/choice_hotels/unmapped_category/{location["brandCode"]}/{location["brandName"]}'
                    )
                    self.crawler.stats.inc_value(f"atp/choice_hotels/unmapped_category/{response.url}")
                    self.logger.warning(
                        "Missing brand mapping for %s, %s", location["brandCode"], location["brandName"]
                    )

                yield item
