from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class UBreakiFixSpider(SitemapSpider, StructuredDataSpider):
    name = "ubreakifix"
    ASURION = {
        "brand": "Asurion Tech Repair & Solutions",
        "brand_wikidata": "Q4811938",
    }
    item_attributes = {"brand": "uBreakiFix", "brand_wikidata": "Q53685733"}
    sitemap_urls = [
        "https://www.ubreakifix.com/us-locations-sitemap.xml",
        "https://www.ubreakifix.com/ca/ca-locations-sitemap.xml",
    ]
    sitemap_rules = [("/locations/", "parse_sd")]

    def pre_process_data(self, ld_data, **kwargs):
        if isinstance(ld_data["openingHours"], str):
            ld_data["openingHours"] = (
                ld_data["openingHours"].replace(": ", " ").replace(" - ", "-").replace("Tues", "Tu")
            )

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "asurion.com" in item["website"]:
            item.update(self.ASURION)
        yield item
