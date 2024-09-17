from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class TsbGBSpider(SitemapSpider, StructuredDataSpider):
    name = "tsb_gb"
    item_attributes = {
        "brand": "TSB",
        "brand_wikidata": "Q7671560",
        "extras": Categories.BANK.value,
    }
    sitemap_urls = ["https://branches.tsb.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/branches\.tsb\.co\.uk\/[-\w]+\/[-\/\w]+\.html$", "parse_sd")]
    wanted_types = ["BankOrCreditUnion", "FinancialService"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["image"] == item["website"]:
            item["image"] = None

        if "phone" in item and item["phone"] is not None and item["phone"].replace(" ", "").startswith("+443"):
            item.pop("phone", None)

        yield item
