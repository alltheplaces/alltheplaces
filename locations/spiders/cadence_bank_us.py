from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CadenceBankUSSpider(SitemapSpider, StructuredDataSpider):
    name = "cadence_bank_us"
    item_attributes = {"brand": "Cadence Bank", "brand_wikidata": "Q4854138"}
    sitemap_urls = ["https://cadencebank.com/sitemap.xml"]
    sitemap_rules = [("/find-a-location/", "parse_sd")]
    time_format = "%H:%M:%S"

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.BANK, item)
        if "ATM" in response.xpath('//*[@class="location-detail-hero-wrapper"]//h3//text()').get():
            apply_yes_no(Extras.ATM, item, True)
        yield item
