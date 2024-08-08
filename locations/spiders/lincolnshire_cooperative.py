import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser


class LincolnshireCooperativeSpider(SitemapSpider):
    name = "lincolnshire_cooperative"
    item_attributes = {
        "brand": "Lincolnshire Co-operative",
        "brand_wikidata": "Q5329759",
    }
    sitemap_urls = ["https://www.lincolnshire.coop/sitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.lincolnshire\.coop\/branches\/(food-stores|pharmacies|funeral-homes|travel-branches|filling-stations|coffee|florist)\/[-\w]+$",
            "parse_item",
        )
    ]
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

    def parse_item(self, response):
        ld_item = response.xpath('//script[@type="application/ld+json"]//text()').get()
        ld_item = json.loads(ld_item.replace('// "addressLocality"', '"addressLocality"'), strict=False)

        item = LinkedDataParser.parse_ld(ld_item)

        if item.get("image"):
            item["image"] = item["image"].replace("https://www.lincolnshire.coophttps://", "https://")

        if item.get("phone"):
            item["phone"] = item["phone"].replace(" (24 hours)", "")

        for label, cat in self.categories:
            if label in item["name"].lower():
                apply_category(cat, item)
                break

        return item
