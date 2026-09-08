import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.structured_data_spider import StructuredDataSpider


class PfgFRSpider(SitemapSpider, StructuredDataSpider):
    name = "pfg_fr"
    item_attributes = {"brand": "PFG", "brand_wikidata": "Q3396087", "name": "PFG"}
    sitemap_urls = ["https://www.pfg.fr/sitemap/agency.xml"]
    # Sitemap also lists department/city listing pages; this keeps only individual agency pages.
    sitemap_rules = [(r"/agence-pompes-funebres-pfg-[\w-]+-(\d+)$", "parse")]
    # robots.txt is DataDome-blocked and fetched before spider code can attach zyte_api meta.
    custom_settings = {"ROBOTSTXT_OBEY": False}
    # twitter:site is the brand's own handle, identical on every page, not a per-location value.
    search_for_twitter = False

    def _parse_sitemap(self, response):
        # httpResponseHeaders is required too, or scrapy-zyte-api returns a binary response with no .selector.
        for request in super()._parse_sitemap(response):
            request.meta["zyte_api"] = {"httpResponseBody": True, "httpResponseHeaders": True, "geolocation": "FR"}
            yield request

    async def start(self):
        async for request in super().start():
            request.meta["zyte_api"] = {"httpResponseBody": True, "httpResponseHeaders": True, "geolocation": "FR"}
            yield request

    def post_process_item(self, item: Feature, response, ld_data: dict, **kwargs):
        apply_category(Categories.SHOP_FUNERAL_DIRECTORS, item)

        # address.addressLocality/addressRegion are lowercase, unaccented slugs; the breadcrumb has clean names.
        item.pop("state", None)
        if breadcrumbs := LinkedDataParser.find_linked_data(response, "BreadcrumbList"):
            for crumb in breadcrumbs.get("itemListElement", []):
                if crumb.get("position") == 3:
                    item["state"] = re.sub(r"\s*\(\d+\)$", "", crumb["name"])
                elif crumb.get("position") == 4:
                    item["city"] = item["branch"] = crumb["name"]

        # JSON-LD "name" format is inconsistent across pages; branch (above) is the reliable one.
        item["name"] = None

        if item.get("street_address"):
            item["street_address"] = " ".join(item["street_address"].split())

        yield item
