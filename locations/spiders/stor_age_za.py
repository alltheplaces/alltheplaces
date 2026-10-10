import json
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class StorAgeZASpider(SitemapSpider):
    name = "stor_age_za"
    item_attributes = {"brand": "Stor-Age", "name": "Stor-Age"}
    sitemap_urls = ["https://stor-age.co.za/sitemaps/stores.xml"]
    sitemap_rules = [(r"/stores/", "parse")]

    def parse(self, response: Response) -> Iterable[Feature]:
        next_data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        page_props = next_data["props"]["pageProps"]
        store = page_props["storeMeta"]["data"]["stores"][0]
        if not store.get("isActive"):
            return
        queries = page_props["initialData"]["props"]["dehydratedState"]["queries"]
        address = queries[0]["state"]["data"]["store"].get("physicalAddress")

        item = Feature()
        item["ref"] = store["locationCode"]
        item["branch"] = store["name"]
        item["lat"] = store["latitude"]
        item["lon"] = store["longitude"]
        item["phone"] = store["contactNumber"]
        item["email"] = store["storeEmail"]
        item["addr_full"] = address
        item["website"] = response.url

        item["opening_hours"] = oh = OpeningHours()
        for rule in store.get("officeHours") or []:
            if not (day_from := rule["dayRange"]["from"]):
                continue
            day_to = rule["dayRange"]["to"] or day_from
            if rule["timeRange"]["closed"]:
                oh.add_ranges_from_string(f"{day_from} - {day_to}: closed")
            else:
                oh.add_ranges_from_string(
                    f"{day_from} - {day_to}: {rule['timeRange']['from'][:5]} - {rule['timeRange']['to'][:5]}"
                )

        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
