import json

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class CcfFRSpider(SitemapSpider, StructuredDataSpider):
    name = "ccf_fr"
    item_attributes = {"brand": "CCF", "brand_wikidata": "Q3006195"}
    allowed_domains = ["agences.ccf.fr"]
    sitemap_urls = ["https://agences.ccf.fr/sitemap_pois.xml"]
    sitemap_rules = [("", "parse_sd")]

    def post_process_item(self, item, response: Response, ld_data):
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        services = (
            data.get("props", {}).get("pageProps", {}).get("poiData", {}).get("customPoiData").get("services", [])
        )
        for service in services:
            apply_yes_no(Extras.ATM, item, service.get("code") == "atm" and service.get("value") is True)
        apply_category(Categories.BANK, item)
        yield item
