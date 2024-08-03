from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class MtBankUSSpider(SitemapSpider, StructuredDataSpider):
    name = "mt_bank_us"
    item_attributes = {"brand": "M&T Bank", "brand_wikidata": "Q3272257"}
    sitemap_urls = ["https://locations.mtb.com/robots.txt"]
    sitemap_rules = [(r"\.html$", "parse_sd")]
    wanted_types = ["FinancialService"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        cat = response.xpath('//span[@class="Hero-locationType"]/text()').get()
        if cat == "ATM Only":
            apply_category(Categories.ATM, item)
            item["located_in"] = item.pop("name")
        elif cat in ["Branch & ATM", "Branch"]:
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, cat == "Branch & ATM")

            if not item["name"].startswith("M&T Bank in "):
                # Duplicates, eg:
                # https://locations.mtb.com/ma/agawam/bank-branches-and-atms-agawam-ma-8422.html
                # https://locations.mtb.com/ma/agawam/bank-branches-and-atms-agawam-ma-sa7000.html
                return
            item["branch"] = item.pop("name").removeprefix("M&T Bank in ")

        item["country"] = "US"

        yield item
