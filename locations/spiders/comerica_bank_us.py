from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider

CATEGORY_MAP = {
    "BankOrCreditUnion": Categories.BANK,
    "AutomatedTeller": Categories.ATM,
    "FinancialService": Categories.OFFICE_FINANCIAL,
}


class ComericaBankUSSpider(SitemapSpider, StructuredDataSpider):
    name = "comerica_bank_us"
    item_attributes = {"brand": "Comerica Bank", "brand_wikidata": "Q1114148"}
    sitemap_urls = ["https://locations.comerica.com/sitemap.xml"]
    sitemap_rules = [("/location/", "parse_sd")]
    wanted_types = list(CATEGORY_MAP.keys())
    search_for_facebook = False
    search_for_twitter = False

    def pre_process_data(self, ld_data, **kwargs):
        if ld_data["location"]["branchCode"] == "None":
            del ld_data["location"]["branchCode"]
        ld_data["location"]["geo"] = ld_data["location"]["address"].pop("geo")
        del ld_data["location"]["@type"]
        ld_data.update(ld_data.pop("location"))

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["extras"]["fax"] = ld_data.get("faxNumber")
        item["extras"]["addr:unit"] = response.xpath("//div[@class='extended-address']/text()").get()
        apply_category(CATEGORY_MAP[ld_data["@type"]], item)

        if ld_data["@type"] == "AutomatedTeller":
            del item["name"]
        else:
            item["branch"] = item.pop("name").strip()
            apply_yes_no(Extras.ATM, item, bool(response.xpath("//h3[text()='ATM']")))

        yield item
