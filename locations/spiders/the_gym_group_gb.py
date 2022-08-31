import json

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class TheGymGroupGBSpider(SitemapSpider):
    name = "the_gym_group_gb"
    item_attributes = {
        "brand": "The Gym Group",
        "brand_wikidata": "Q48815022",
        "country": "GB",
    }
    sitemap_urls = ["https://www.thegymgroup.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.thegymgroup\.com\/find-a-gym\/[-\w]+-gyms\/[-\w]+\/$",
            "parse",
        )
    ]

    def parse(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())

        if data is None:
            return

        store = data["props"].get("pageProps")

        if store is None:
            return

        item = DictParser.parse(store)

        item["ref"] = store.get("branchId")

        item["name"] = store.get("gymName")

        if addr := store.get("address"):
            item["street_address"] = ", ".join(
                filter(
                    None,
                    [addr.get("address1"), addr.get("address2"), addr.get("address3")],
                )
            )

        item["website"] = response.url

        oh = OpeningHours()
        if rules := store.get("openingHours"):
            for day, rule in rules.items():
                oh.add_range(
                    day[0:2],
                    rule["OpeningTime"],
                    rule["ClosingTime"],
                    time_format="%H:%M:%S",
                )

        item["opening_hours"] = oh.as_opening_hours()

        return item
