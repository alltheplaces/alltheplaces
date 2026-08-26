from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LandmarkCreditUnionUSSpider(SitemapSpider, StructuredDataSpider):
    name = "landmark_credit_union_us"
    item_attributes = {"brand": "Landmark Credit Union", "brand_wikidata": "Q16999087"}
    sitemap_urls = ["https://www.landmarkcu.com/robots.txt"]
    sitemap_rules = [(r"/atm-branch-locations/.+", "parse_sd")]
    wanted_types = ["BankOrCreditUnion"]
    drop_attributes = {"image", "phone"}  # image is an unresolved template placeholder; phone is a shared hotline

    def pre_process_data(self, ld_data: dict, **kwargs):
        # Saturday hours are only present nested under "department", not in the
        # top-level openingHoursSpecification, so merge them in before parsing.
        specs = ld_data.get("openingHoursSpecification") or []
        if not isinstance(specs, list):
            specs = [specs]
        for department in ld_data.get("department", []):
            if dept_spec := department.get("openingHoursSpecification"):
                specs.append(dept_spec)
        ld_data["openingHoursSpecification"] = specs

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Landmark Credit Union - ").removesuffix(" Branch")
        item["name"] = self.item_attributes["brand"]

        if item.get("lon") is not None and item["lon"] > 0:
            # Wauwatosa branch publishes longitude == latitude on the source page; drop rather than ship garbage
            item["lat"] = None
            item["lon"] = None

        apply_category(Categories.BANK, item)

        yield item
