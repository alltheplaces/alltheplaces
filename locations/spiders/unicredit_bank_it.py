import re
from typing import Any

import chompjs
from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class UnicreditBankITSpider(CrawlSpider):
    name = "unicredit_bank_it"
    item_attributes = {"brand": "UniCredit Bank", "brand_wikidata": "Q45568"}
    start_urls = ["https://www.unicredit.it/it/contatti-e-agenzie/lista-agenzie.html"]
    rules = [
        Rule(LinkExtractor(allow=r"/contatti-e-agenzie/lista-agenzie/[a-z]{2}\.html$")),
        Rule(LinkExtractor(allow=r"/contatti-e-agenzie/lista-agenzie/[a-z]{2}/[-\w]+\.html$")),
        Rule(LinkExtractor(allow=r"/contatti-e-agenzie/lista-agenzie/[a-z]{2}/[-\w]+/[-\w]+\.html$"), callback="parse"),
    ]
    url_match = re.compile(r"url[:\s]+\'(.+?)\'")
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 180, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        website = response.url
        for url in re.findall(self.url_match, response.text):
            if "AgencyLocator" in url:
                yield Request(url, callback=self.parse_branches, cb_kwargs=dict(website=website))
            elif "ATMLocator" in url:
                yield Request(url, callback=self.parse_atms, cb_kwargs=dict(website=website))
            else:
                continue

    def parse_branches(self, response: Response, website: str) -> Any:
        locations = chompjs.parse_js_object(response.text)
        if locations.get("total") == 0:
            return
        for location in locations["layers"][0].get("objects", []):
            coordinates = location["geom"]
            location = location["data"]["main"]
            item = Feature()
            item["lat"] = coordinates.get("lat")
            item["lon"] = coordinates.get("lng")
            item["ref"] = location.get("TG_COD_DIP")
            item["street_address"] = location.get("TG_VIA_FIL")
            item["city"] = location.get("TG_LOC_FIL")
            item["state"] = location.get("TG_SGL_PRO")
            item["postcode"] = location.get("TG_CAP_FIL")

            for contact_type in ["TEL", "FAX"]:
                contact = (
                    location[f"TG_{contact_type}_PRN"] + location[f"TG_{contact_type}_NUM"]
                    if location.get(f"TG_{contact_type}_PRN")
                    else location.get(f"TG_{contact_type}_NUM")
                )
                if contact_type == "TEL":
                    item["phone"] = contact
                else:
                    item["extras"]["fax"] = contact

            item["email"] = location.get("TG_IN_MAIL")
            item["website"] = website
            item["opening_hours"] = self.parse_opening_hours(location)
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, location.get("ATM") == "1")
            yield item

    def parse_atms(self, response: Response, website: str) -> Any:
        locations = chompjs.parse_js_object(response.text)
        if locations.get("total") == 0:
            return
        for location in locations["layers"][0].get("objects", []):
            coordinates = location["geom"]
            location = location["data"]["main"]
            item = Feature()
            item["lat"] = coordinates.get("lat")
            item["lon"] = coordinates.get("lng")
            item["ref"] = location.get("TG_COD_DIP") + "-" + location.get("TG_COD_ATM")
            item["street_address"] = location.get("TG_INDIRIZZO_ATM")
            item["city"] = location.get("TG_LOCALITA")
            item["state"] = location.get("TG_PROVINCIA")
            item["website"] = website
            apply_category(Categories.ATM, item)
            yield item

    def parse_opening_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_3_LETTERS:
            for shift in ["AM", "PM"]:
                if hours := location.get(f"TG_OPEN_{day.upper()}_{shift}"):
                    oh.add_range(day, hours[:4], hours[4:], "%H%M")
        return oh
