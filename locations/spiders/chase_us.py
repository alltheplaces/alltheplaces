from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class ChaseUSSpider(SitemapSpider, StructuredDataSpider):
    name = "chase_us"
    item_attributes = {"brand": "Chase", "brand_wikidata": "Q524629"}
    drop_attributes = {"image"}
    allowed_domains = ["locator.chase.com"]
    sitemap_urls = ["https://locator.chase.com/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/locator\.chase\.com\/(?!es)[a-z]{2}\/[\w\-]+\/[\w\-]+$", "parse_sd")]
    search_for_facebook = False
    search_for_twitter = False

    def pre_process_data(self, ld_data, **kwargs):
        for i in range(0, len(ld_data.get("openingHours", []))):
            ld_data["openingHours"][i] = ld_data["openingHours"][i].replace("00:00-00:00", "Closed")

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["name"] == "Chase Bank":
            item.pop("name")
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, "ATM services" in response.text)
        elif item["name"] == "Chase ATM":
            apply_category(Categories.ATM, item)

        yield item
