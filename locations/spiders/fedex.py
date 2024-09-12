from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.settings import ITEM_PIPELINES
from locations.structured_data_spider import StructuredDataSpider


class FedexSpider(SitemapSpider, StructuredDataSpider):
    name = "fedex"
    item_attributes = {"brand": "FedEx", "brand_wikidata": "Q459477"}
    sitemap_urls = [
        "https://local.fedex.com/sitemap.xml",
    ]
    sitemap_rules = [
        (r"\/[a-z0-9]{4,5}$", "parse_sd"),
        (r"\/office-[0-9]{4}$", "parse_sd"),
    ]
    wanted_types = ["LocalBusiness"]
    custom_settings = {  # Disable NSI matching
        "ITEM_PIPELINES": ITEM_PIPELINES | {"locations.pipelines.apply_nsi_categories.ApplyNSICategoriesPipeline": None}
    }
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["email"] = response.xpath('//a[@class="Hero-emailLink Link--primary"]/@href').extract_first()
        if item["email"]:
            item["email"] = item["email"][5:]

        item["city"] = response.xpath('//span[@class="Address-field Address-city"]/text()').extract_first()

        item["image"] = None

        if "FedEx Office Print & Ship Center" in item["name"]:
            item["name"] = "FedEx Office Print & Ship Center"
            apply_category(Categories.SHOP_COPYSHOP, item)
        elif "FedEx at " in item["name"]:
            item["located_in"] = item.pop("name").split("FedEx at ")[1]
            apply_category({"post_office": "post_partner"}, item)
        elif "FedEx Authorized ShipCenter" in item["name"]:
            item["located_in"] = item["name"].replace("FedEx Authorized ShipCenter ", "")
            item["name"] = "FedEx Authorized ShipCenter"
            apply_category({"post_office": "post_partner"}, item)
        elif "FedEx OnSite" in item["name"]:
            item["located_in"] = item.pop("name").replace("FedEx OnSite", "").strip()
            apply_category({"post_office": "post_partner"}, item)
        elif item["name"] == "FedEx Station":
            apply_category(Categories.POST_DEPOT, item)
        elif item["name"] == "FedEx Ship Center":
            apply_category(Categories.POST_OFFICE, item)
        elif "FedEx Office Ship Center" in item["name"]:
            item["name"] = "FedEx Office Ship Center"
            apply_category(Categories.POST_OFFICE, item)
        elif "FedEx Express Poland" in item["name"]:
            item["name"] = item["brand"] = "FedEx Express"
            apply_category(Categories.POST_OFFICE, item)
        elif "FedEx Location" in item["name"]:
            item["located_in"] = item.pop("name").split(" FedEx Location")[0]
            apply_category({"post_office": "post_partner"}, item)

        yield item
