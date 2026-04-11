from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ZdrofitPLSpider(SitemapSpider, StructuredDataSpider):
    name = "zdrofit_pl"
    item_attributes = {
        "brand": "Zdrofit",
        "brand_wikidata": "Q113457353",
    }
    time_format = "%H:%M:%S"
    sitemap_urls = ["https://zdrofit.pl/sitemaps/clubs-1.xml"]
    sitemap_rules = [
        (r"https://zdrofit.pl/kluby-fitness/[a-z0-9-]+/$", "parse_sd"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.GYM, item)
        item["branch"] = item["name"]
        item["name"] = "Zdrofit"
        if response.xpath('//*[contains(text(), "Sauna")]'):
            item["extras"]["sauna"] = "yes"
        if response.xpath('//*[contains(text(), "WiFi")]'):
            item["extras"]["internet_access"] = "wlan"
        yield item
