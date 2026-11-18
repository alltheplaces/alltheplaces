import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class WestCoastSelfStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "west_coast_self_storage_us"
    item_attributes = {"brand": "West Coast Self-Storage", "brand_wikidata": "Q110084888"}
    sitemap_urls = ["https://www.westcoastselfstorage.com/page-sitemap.xml"]
    sitemap_rules = [(r"/self-storage/[a-z-]+/[^/]+(/[^/]+)?/$", "parse_sd")]
    wanted_types = ["SelfStorage"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        address_link = response.xpath('//a[contains(@href, "maps.app.goo.gl")]')
        if not address_link:
            return
        item["ref"] = address_link[0].xpath("@href").get().rstrip("/").split("/")[-1]
        item["branch"] = item.pop("name").removeprefix("West Coast Self-Storage").strip() or None
        address_parts = [part.strip() for part in address_link[0].xpath(".//text()").getall() if part.strip()]
        item["addr_full"] = " ".join(dict.fromkeys(address_parts))
        extract_google_position(item, response)

        if periods := response.xpath(
            '//div[contains(@class, "wcss-gbp-hours-section-office")]//@data-wcss-regular-periods'
        ).get():
            item["opening_hours"] = oh = OpeningHours()
            for period in json.loads(periods):
                oh.add_range(
                    period["openDay"].title(),
                    "{:02d}:{:02d}".format(period["openTime"].get("hours", 0), period["openTime"].get("minutes", 0)),
                    "{:02d}:{:02d}".format(period["closeTime"].get("hours", 0), period["closeTime"].get("minutes", 0)),
                )

        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
