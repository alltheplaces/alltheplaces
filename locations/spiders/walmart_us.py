import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class WalmartUSSpider(SitemapSpider):
    name = "walmart_us"
    item_attributes = {"brand": "Walmart", "brand_wikidata": "Q483551"}
    allowed_domains = ["walmart.com"]
    sitemap_urls = ["https://www.walmart.com/sitemap_store_main.xml"]
    sitemap_rules = [("", "parse_store")]
    requires_proxy = True

    CATEGORIES = {
        "GAS_STATION": Categories.FUEL_STATION,
        "PHARMACY": Categories.PHARMACY,
        "STORE": Categories.SHOP_SUPERMARKET,
    }

    def store_hours(self, store):
        if store.get("open24Hours") is True:
            return "24/7"
        elif rules := store.get("operationalHours"):
            oh = OpeningHours()
            for rule in rules:
                if rule.get("closed") is True:
                    continue

                oh.add_range(rule.get("day")[:2], rule.get("start"), rule.get("end"))

            return oh.as_opening_hours()

    def parse_store(self, response):
        script = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()

        if script is None:
            return

        data = json.loads(script)

        if data is None:
            return

        store = data["props"]["pageProps"]["initialData"]["initialDataNodeDetail"]["data"]["nodeDetail"]

        if store is None:
            return

        item = DictParser.parse(store)

        item["phone"] = store.get("phoneNumber")
        item["name"] = store.get("displayName")
        item["opening_hours"] = self.store_hours(store)

        if addr := store.get("address"):
            item["street_address"] = clean_address(
                [
                    addr.get("addressLineOne"),
                    addr.get("addressLineTwo"),
                ]
            )
        item["website"] = response.url

        for service in store["services"]:
            if service["name"] not in ["PHARMACY", "GAS_STATION"]:
                self.crawler.stats.inc_value("atp/walmart/ignored/{}".format(service["name"]))
                continue
            poi = item.copy()
            poi["ref"] += service["name"]
            poi["name"] = service["displayName"]
            poi["phone"] = service["phone"]
            poi["opening_hours"] = self.store_hours(service)

            apply_category(self.CATEGORIES[service["name"]], poi)

            yield poi

        item["extras"]["type"] = store.get("type")
        self.crawler.stats.inc_value("atp/walmart/type/{}".format(store.get("type")))  # TODO revisit after weekly
        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
