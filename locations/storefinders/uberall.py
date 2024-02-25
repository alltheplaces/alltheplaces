import logging
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class UberallSpider(Spider, AutomaticSpiderGenerator):
    dataset_attributes = {"source": "api", "api": "uberall.com"}

    key = ""
    business_id_filter = None

    def start_requests(self):
        yield JsonRequest(url=f"https://uberall.com/api/storefinders/{self.key}/locations/all")

    def parse(self, response, **kwargs):
        if response.json()["status"] != "SUCCESS":
            logging.warning("Request failed")

        for feature in response.json()["response"]["locations"]:
            if self.business_id_filter:
                if feature["businessId"] != self.business_id_filter:
                    continue

            feature["street_address"] = ", ".join(filter(None, [feature["streetAndNumber"], feature["addressExtra"]]))
            feature["ref"] = feature.get("identifier")

            item = DictParser.parse(feature)

            item["image"] = ";".join(filter(None, [p.get("publicUrl") for p in feature["photos"] or []]))

            oh = OpeningHours()
            for rule in feature["openingHours"]:
                if rule.get("closed"):
                    continue
                # I've only seen from1 and from2, but I guess it could any length
                for i in range(1, 3):
                    if rule.get(f"from{i}") and rule.get(f"to{i}"):
                        oh.add_range(
                            DAYS[rule["dayOfWeek"] - 1],
                            rule[f"from{i}"],
                            rule[f"to{i}"],
                        )
            item["opening_hours"] = oh.as_opening_hours()

            yield from self.parse_item(item, feature)

    def parse_item(self, item, feature, **kwargs):
        yield item

    def storefinder_exists(response: Response) -> bool | Request:
        if response.xpath('//div[@id="store-finder-widget"]/@data-key').get():
            return True

        # Example: https://www.yves-rocher.it/trova-il-tuo-negozio#!
        # <script src="https://uberall.com/assets/storeFinderWidget-v2.js"></script>
        if response.xpath('//script[contains(@src, "https://uberall.com/assets/storeFinderWidget-v2.js")]').get():
            return True

        # Example: https://www.aldi.pl/informacje-dla-klienta/wyszukiwarka-sklepu.html
        # Example: https://www.hypovereinsbank.de/hvb/kontaktwege/filiale
        # TODO: Needs playwright to detect this properly in most cases
        # Loads into the DOM:
        # <script type="module" src="https://locator.uberall.com/locator-assets/store-finder-widget-bundle-v2-modern.js?b=My4xODQuMjU="></script>
        if response.xpath(
            '//script[contains(@src, "https://locator.uberall.com/locator-assets/store-finder-widget-bundle-v2-modern.js")]'
        ).get():
            return True

        return False

    def extract_spider_attributes(response: Response) -> dict | Request:
        if response.xpath('//div[@id="store-finder-widget"]/@data-key').get():
            return {"key": response.xpath('//div[@id="store-finder-widget"]/@data-key').get()}
