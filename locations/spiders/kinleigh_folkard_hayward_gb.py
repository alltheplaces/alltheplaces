from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class KinleighFolkardHaywardGBSpider(SitemapSpider, StructuredDataSpider):
    name = "kinleigh_folkard_hayward_gb"
    item_attributes = {"brand": "Kinleigh Folkard & Hayward", "country": "GB"}
    sitemap_urls = ["https://www.kfh.co.uk/sitemap-pages.xml"]
    sitemap_rules = [(r"^https://www\.kfh\.co\.uk/branch-finder/[^/]+$", "parse_sd")]
    wanted_types = ["RealEstateAgent"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        branch = response.xpath("//h1/text()").get()
        item["branch"] = (branch or "").removesuffix(" Estate Agents") or None
        item["name"] = self.item_attributes["brand"]
        item["street_address"] = None
        item["addr_full"] = ld_data.get("address", {}).get("streetAddress")

        if opening_hours := ld_data.get("openingHours"):
            item["opening_hours"].add_ranges_from_string(opening_hours)

        apply_category(Categories.OFFICE_ESTATE_AGENT, item)

        yield item
