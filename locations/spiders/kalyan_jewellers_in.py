import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class KalyanJewellersINSpider(SitemapSpider, JSONBlobSpider):
    name = "kalyan_jewellers_in"
    item_attributes = {"brand": "Kalyan Jewellers", "brand_wikidata": "Q6354854"}
    sitemap_urls = ["https://store.kalyanjewellers.net/sitemap.xml"]
    sitemap_rules = [(r"/sitemap\.xml\?storeId=", "_parse_sitemap"), (r"/overview$", "parse")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    drop_attributes = {"name", "email", "addr_full"}

    def extract_json(self, response):
        feature = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"][
            "stores"
        ]
        return [feature] if feature["country"] == "India" and not feature["storeName"].startswith("My Kalyan") else []

    def post_process_item(self, item, response, feature):
        item["website"] = response.url
        item["street_address"] = merge_address_lines([feature["address"], feature["locality"]])
        item["postcode"] = feature["pincode"]
        if feature["phone"] in (None, "18004257333"):
            item["phone"] = next(
                (mapping["mappingNumber"] for mapping in feature["CallMaps"] if mapping["isActive"]), None
            )
        if feature["metaData"] and (times := feature["metaData"].get("Mon - Sun")):
            open_time, close_time = times.split(" to ")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_days_range(DAYS, open_time, close_time, time_format="%I:%M %p")
        apply_category(Categories.SHOP_JEWELRY, item)
        yield item
