import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class MeijerUSSpider(SitemapSpider):
    name = "meijer_us"
    item_attributes = {"brand": "Meijer", "brand_wikidata": "Q1917753", "extras": Categories.SHOP_SUPERMARKET.value}
    user_agent = BROWSER_DEFAULT
    requires_proxy = True
    sitemap_urls = ["https://www.meijer.com/bin/meijer/store-sitemap.xml"]
    allowed_domains = ["www.meijer.com"]
    store_url = re.compile(r"https://www\.meijer\.com/shopping/store-locator/(\d+)\.html")

    # Only use the sitemap to get a list of store IDs. Get the actual store info from the API.
    def sitemap_filter(self, entries):
        for entry in entries:
            if match := self.store_url.match(entry["loc"]):
                store_id = match.group(1)
                yield {"loc": f"https://www.meijer.com/bin/meijer/store/details?storeId={store_id}"}

    def parse(self, response):
        location = response.json()
        item = DictParser.parse(location)
        item["country"], item["state"] = location["address"]["region"]["isocode"].split("-")
        item["branch"] = location["displayName"]
        item["ref"] = item.pop("name")
        item["website"] = f"https://www.meijer.com/shopping/store-locator/{item['ref']}.html"
        apply_yes_no(Extras.DELIVERY, item, location["deliveryEligibility"])

        if location["openingHours"]["is24Hrsand365Days"]:
            item["opening_hours"] = "24/7"
        else:
            oh = OpeningHours()
            for row in location["openingHours"]["weekDayOpeningList"]:
                day = row["weekDay"]
                if " - " in day:
                    days_range = day.split(" - ")
                    days = DAYS_3_LETTERS[
                        DAYS_3_LETTERS.index(days_range[0]) : DAYS_3_LETTERS.index(days_range[-1]) + 1
                    ]
                else:
                    days = [day]
                if row["closed"]:
                    oh.set_closed(days)
                else:
                    oh.add_days_range(
                        days,
                        row["openingTime"]["formattedHour"],
                        row["closingTime"]["formattedHour"],
                        time_format="%I:%M %p",
                    )
            item["opening_hours"] = oh

        yield item
