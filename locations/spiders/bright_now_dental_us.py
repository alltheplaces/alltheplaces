from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BrightNowDentalUSSpider(SitemapSpider, StructuredDataSpider):
    name = "bright_now_dental_us"
    item_attributes = {
        "brand": "Bright Now! Dental",
        "brand_wikidata": "Q108286875",
    }
    sitemap_urls = ["https://www.brightnow.com/wp-content/uploads/custom-sitemaps/1/locations-sitemap.xml"]
    sitemap_rules = [
        (r"^https://www\.brightnow\.com/dental-office/[\w-]+/\d+/$", "parse"),
    ]
    search_for_facebook = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Bright Now! Dental - ")
        item["ref"] = response.url.split("/")[-2]
        yield item
