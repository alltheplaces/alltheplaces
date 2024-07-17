import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class NissanEUSpider(scrapy.Spider):
    name = "nissan_eu"
    item_attributes = {
        "brand": "Nissan",
        "brand_wikidata": "Q20165",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}
    COUNTRY_DEALER_LOCATOR_SLUGS = [
        ("be", "nl", "e70c", "5fe8", "6ff2"),
        ("es", "es", "5aba", "51e", "14d"),
        ("de", "de", "", "9ad4", "14d"),
        ("dk", "da", "e70c", "5fe8", "14d"),
        ("ee", "et", "e70c", "5fe8", "14d"),
        ("fi", "fi", "", "6ad1", "14d"),
        ("fr", "fr", "", "2910", "ff88"),
        ("gf", "fr", "e70c", "5fe8", "14d"),
        ("mq", "fr", "e70c", "5fe8", "14d"),
        ("it", "it", "", "f9ac", "14d"),
        ("nl", "nl", "e70c", "5fe8", "14d"),
        ("lt", "lt", "e70c", "5fe8", "14d"),
        ("lu", "fr", "e70c", "5fe8", "14d"),
        ("lv", "lv", "e70c", "5fe8", "14d"),
        ("no", "no", "", "22b6", "14d"),
        ("ua", "uk", "e70c", "5fe8", "14d"),
    ]

    def start_requests(self):
        for country, lang, slug_1, slug_2, slug_3 in self.COUNTRY_DEALER_LOCATOR_SLUGS:
            if not slug_1:
                yield JsonRequest(
                    url=f"https://www.nissan.{country}/content/nissan_prod/{lang}_{country.upper()}/index/dealer-finder/jcr:content/freeEditorial/columns12_{slug_2}/col1-par/find_a_dealer_{slug_3}.extended_dealers_by_location.json/page/1/_charset_/utf-8/size/-1/data.json",
                )
            else:
                yield JsonRequest(
                    url=f"https://www.nissan.{country}/content/nissan_prod/{lang}_{country.upper()}/index/dealer-finder/jcr:content/freeEditorial/contentzone_{slug_1}/columns/columns12_{slug_2}/col1-par/find_a_dealer_{slug_3}.extended_dealers_by_location.json/page/1/_charset_/utf-8/size/-1/data.json".replace(
                        "gf", "fr"
                    ).replace(
                        "mq", "fr"
                    ),
                )

    def parse(self, response):
        for data in response.json().get("dealers"):
            item = DictParser.parse(data)
            item["name"] = data.get("tradingName")
            item["country"] = data.get("country").upper()
            item["website"] = data.get("contact", {}).get("website") or "https://www.nissan-europe.com/"
            if item["website"].startswith("/"):
                item["website"] = response.urljoin(item["website"])

            services = [s["iconId"].removeprefix("icon-") for s in data.get("dealerServices", [])]
            if "car" in services:
                apply_category(Categories.SHOP_CAR, item)
                if "configure" in services:
                    apply_yes_no("service:vehicle:car_repair", item, True)
            elif "configure" in services:
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            else:
                apply_category(Categories.SHOP_CAR, item)

            yield item
