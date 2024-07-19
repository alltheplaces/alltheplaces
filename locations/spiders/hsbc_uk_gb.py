from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class HsbcUkGBSpider(SitemapSpider, StructuredDataSpider):
    name = "hsbc_uk_gb"
    item_attributes = {"brand": "HSBC UK", "brand_wikidata": "Q64767453", "extras": Categories.BANK.value}
    start_urls = ["https://www.hsbc.co.uk/branch-list/"]
    sitemap_urls = ["https://www.hsbc.co.uk/sitemaps-pages.xml"]
    sitemap_rules = [(r"/branch-list/.+", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["name"] = item["name"].split(" - ", 2)[1]
        item.pop("image", None)
        item.pop("facebook", None)
        item.pop("twitter", None)
        extra_features = [feature["itemOffered"]["name"] for feature in ld_data["hasOfferCatalog"]["itemListElement"]]
        apply_yes_no(Extras.ATM, item, len(list(filter(lambda x: " ATM" in x.upper(), extra_features))) > 0, False)
        apply_yes_no(Extras.WIFI, item, "Wi-Fi" in extra_features, False)
        yield item
