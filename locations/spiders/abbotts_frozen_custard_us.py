from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.tom_wahls_us import TomWahlsUSSpider


class AbbottsFrozenCustardUSSpider(SitemapSpider):
    name = "abbotts_frozen_custard_us"
    item_attributes = {"brand": "Abbott's Frozen Custard", "brand_wikidata": "Q4664334"}
    sitemap_urls = ["https://www.abbottscustard.com/sitemap_index.xml"]
    sitemap_rules = [("/location/", "parse")]
    days = DAYS_EN

    LOCATED_IN_MAPPINGS = [
        (["bill-grays", "bill gray"], {"brand": "Bill Gray's", "brand_wikidata": "Q4909199"}),
        (["tom-wahls", "tom wahl"], TomWahlsUSSpider.item_attributes),
    ]

    def parse(self, response: Response, **kwargs):
        item = Feature()
        item["branch"] = response.xpath("//h1/text()").get()
        item["addr_full"] = merge_address_lines(response.xpath("//address//text()").getall())
        item["phone"] = response.xpath("//h2[text()='Phone']/following-sibling::p/text()").get()
        item["ref"] = item["website"] = response.url

        # All Abbott's locations are ice cream shops
        apply_category(Categories.ICE_CREAM, item)

        # Add parent venue information for locations inside other restaurants
        if branch := item.get("branch"):
            item["located_in"], item["located_in_wikidata"] = extract_located_in(branch, self.LOCATED_IN_MAPPINGS)
            if not item["located_in"] or not item["located_in_wikidata"]:
                if website := item.get("website"):
                    item["located_in"], item["located_in_wikidata"] = extract_located_in(
                        website, self.LOCATED_IN_MAPPINGS
                    )

        yield item
