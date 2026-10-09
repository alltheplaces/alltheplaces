import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class SafewaySpider(SitemapSpider, StructuredDataSpider):
    name = "safeway"
    item_attributes = {
        "brand": "Safeway",
        "brand_wikidata": "Q1508234",
        "country": "US",
    }
    allowed_domains = ["safeway.com"]
    sitemap_urls = [
        "https://local.safeway.com/sitemap.xml",
        "https://local.pharmacy.safeway.com/sitemap.xml",
        "https://local.fuel.safeway.com/sitemap.xml",
    ]
    sitemap_rules = [
        (r"^https://local\.(?:fuel\.|pharmacy\.)?safeway\.com/safeway/\w\w/[-\w]+/[-\w]+\.html$", "parse_sd")
    ]
    wanted_types = ["GroceryStore", "GasStation", "Pharmacy"]
    drop_attributes = {"image"}
    search_for_email = False
    search_for_image = False
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "DOWNLOAD_DELAY": 0.25,
    }

    def pre_process_data(self, ld_data, **kwargs):
        ld_data.pop("openingHours", None)
        ld_data.pop("openingHoursSpecification", None)

    def post_process_item(self, item, response, ld_data, **kwargs):
        if store_id := response.xpath("//*[@data-entity-id]/@data-entity-id").get():
            item["ref"] = store_id

        if raw_days := response.xpath("//@data-days").get():
            oh = OpeningHours()
            for day in json.loads(raw_days):
                if day.get("isClosed"):
                    oh.set_closed(day["day"])
                    continue

                for interval in day.get("intervals", []):
                    oh.add_range(
                        day=day.get("day"),
                        open_time=f"{interval['start']:04d}",
                        close_time=f"{interval['end']:04d}",
                        time_format="%H%M",
                    )
            item["opening_hours"] = oh

        if ld_data["@type"] == "GroceryStore":
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif ld_data["@type"] == "GasStation":
            apply_category(Categories.FUEL_STATION, item)
        elif ld_data["@type"] == "Pharmacy":
            apply_category(Categories.PHARMACY, item)
        yield item
