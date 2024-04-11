from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class WellGBSpider(SitemapSpider, StructuredDataSpider):
    name = "well_gb"
    item_attributes = {"brand": "Well Pharmacy", "brand_wikidata": "Q7726524"}
    sitemap_urls = ["https://finder.well.co.uk/robots.txt"]
    sitemap_rules = [("/store/", "parse")]
    wanted_types = ["Pharmacy"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = response.url
        item["image"] = item["email"] = None

        if postcode := item.get("postcode"):
            if " " not in postcode:
                item["postcode"] = "{} {}".format(postcode[: len(postcode) - 3], postcode[len(postcode) - 3 :])

        yield item
