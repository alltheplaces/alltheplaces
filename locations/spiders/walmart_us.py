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
        "GAS_STATION": None,  # It may be Walmart or Murphy
        "PHARMACY": Categories.PHARMACY,
        "STORE": None,
    }

    def store_hours(self, store) -> OpeningHours | str:
        if store.get("open24Hours") is True:
            return "24/7"
        elif rules := store.get("operationalHours"):
            oh = OpeningHours()
            for rule in rules:
                if rule.get("closed") is True:
                    oh.set_closed(rule["day"])
                else:
                    oh.add_range(rule["day"], rule["start"], rule["end"])

            return oh

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
            if not self.CATEGORIES.get(service["name"]):
                self.crawler.stats.inc_value("atp/walmart/ignored/{}".format(service["name"]))
                continue
            poi = item.deepcopy()
            poi["ref"] += service["name"]
            poi["name"] = service["displayName"]
            poi["phone"] = service["phone"]
            poi["opening_hours"] = self.store_hours(service)

            apply_category(self.CATEGORIES[service["name"]], poi)

            yield poi

        if item["name"].endswith("Supercenter"):
            item["name"] = "Walmart Supercenter"
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif item["name"].endswith("Neighborhood Market"):
            item["name"] = "Walmart Neighborhood Market"
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif item["name"].endswith(" Walmart Pickup Store"):
            item["name"] = "Walmart Pickup Store"
            apply_category(Categories.SHOP_OUTPOST, item)
        elif item["name"].endswith("Store"):
            item["name"] = "Walmart"
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        elif item["name"].endswith("Pharmacy"):
            item["name"] = "Walmart Pharmacy"
            apply_category(Categories.PHARMACY, item)
        elif item["name"].endswith("Gas Station"):
            item["name"] = "Walmart"
            item["brand_wikidata"] = "Q62606411"
            apply_category(Categories.FUEL_STATION, item)
        else:
            self.logger.error("Unknown store format: {}".format(item["name"]))

        yield item
