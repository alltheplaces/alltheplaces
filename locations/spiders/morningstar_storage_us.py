from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MorningstarStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "morningstar_storage_us"
    item_attributes = {"brand": "Morningstar Storage", "brand_wikidata": "Q123029115"}
    sitemap_urls = ["https://www.morningstarstorage.com/sitemaps-1-section-storageLocations-1-sitemap.xml"]
    sitemap_rules = [(r"/locations/[^/]+/\d+/", "parse_sd")]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response, ld_data, **kwargs):
        if not item.get("lat"):
            return
        item["branch"] = item.pop("name", "").removeprefix("Morningstar of ")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            " ".join(response.css(".location-details-hours > div").xpath(".//text()").getall())
        )
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
