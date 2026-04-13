from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ZdrofitPLSpider(SitemapSpider, StructuredDataSpider):
    name = "zdrofit_pl"
    item_attributes = {"brand": "Zdrofit", "brand_wikidata": "Q113457353"}
    time_format = "%H:%M:%S"
    sitemap_urls = ["https://zdrofit.pl/sitemaps/clubs-1.xml"]
    sitemap_rules = [(r"https://zdrofit.pl/kluby-fitness/[a-z0-9-]+/$", "parse_sd")]
    proxy_required = True

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_yes_no("sauna", item, response.xpath('//*[contains(text(), "Sauna")]'))
        apply_yes_no(Extras.WIFI, item, response.xpath('//*[contains(text(), "WiFi")]'))
        apply_category(Categories.GYM, item)
        yield item
