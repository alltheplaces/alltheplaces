from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CaseysGeneralStoreSpider(SitemapSpider, StructuredDataSpider):
    name = "caseys_general_store"
    item_attributes = {"brand": "Casey's General Store", "brand_wikidata": "Q2940968"}
    allowed_domains = ["www.caseys.com"]
    sitemap_urls = ["https://www.caseys.com/sitemap.xml"]
    sitemap_follow = [r"https://www.caseys.com/medias/sys_master/root/.*/Store-en-USD-.*.xml"]
    sitemap_rules = [(r"^https://www\.caseys\.com/general-store/[^/]+/[^/]+/(\d+)$", "parse")]
    wanted_types = ["Restaurant"]
    time_format = "%I:%M%p"
    requires_proxy = True

    def pre_process_data(self, ld_data: dict, **kwargs):
        ld_data["name"] = ld_data["url"] = ld_data["@id"] = None
        for rule in ld_data["openingHoursSpecification"]:
            if rule.get("opens") == rule.get("closes") == "24 hrs":
                rule["opens"] = "12:00am"
                rule["closes"] = "11:59pm"
