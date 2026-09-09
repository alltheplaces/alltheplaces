from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class LincolnshireCooperativeSpider(SitemapSpider, StructuredDataSpider):
    name = "lincolnshire_cooperative"
    item_attributes = {"brand": "Lincolnshire Co-op", "brand_wikidata": "Q6551231", "nsi_id": "N/A"}
    sitemap_urls = ["https://www.lincolnshire.coop/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.lincolnshire\.coop\/branches\/(food-stores|pharmacies|funeral-homes|travel-branches|filling-stations|coffee|florist)\/[-\w]+$",
            "parse_sd",
        )
    ]
    # The ld+json blob contains stray "//" comments, which json5 tolerates
    json_parser = "json5"
    categories = [
        ("food store", Categories.SHOP_CONVENIENCE),
        ("pharmacy", Categories.PHARMACY),
        ("funeral", Categories.SHOP_FUNERAL_DIRECTORS),
        ("florist", Categories.SHOP_FLORIST),
        ("coffee", Categories.COFFEE_SHOP),
        ("filling station", Categories.FUEL_STATION),
        ("travel", Categories.SHOP_TRAVEL_AGENCY),
        ("chiropody", Categories.SHOP_ORTHOPEDICS),
        ("podiatry", Categories.SHOP_ORTHOPEDICS),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item.get("image"):
            # Source data has a malformed protocol-relative URL (e.g. "//www.lincolnshire.coophttps://...")
            # which the base StructuredDataSpider urljoin()s against the response URL, doubling up the scheme.
            item["image"] = "https://" + item["image"].split("https://")[-1]

        if item.get("phone"):
            item["phone"] = item["phone"].replace(" (24 hours)", "")

        for label, cat in self.categories:
            if label in item["name"].lower():
                apply_category(cat, item)
                break

        yield item
