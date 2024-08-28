from scrapy import Selector

from locations.storefinders.wp_go_maps import WpGoMapsSpider

MOCHACHOS_BRANDS = {
    "3": {"brand": "Bacini's"},  # Only 1 and 2 co-located, so no wikidata
    "2": {"brand_wikidata": "Q116619140", "brand": "Skippers"},
    "1": {"brand_wikidata": "Q116619117", "brand": "Mochachos"},
}


class MochachosSpider(WpGoMapsSpider):
    name = "mochachos"
    item_attributes = {
        "brand_wikidata": "Q116619117",
        "brand": "Mochachos",
    }
    allowed_domains = [
        "www.mochachos.com",
    ]

    def post_process_item(self, item, location):
        sel = Selector(text=location["description"])
        item["phone"] = "; ".join(sel.xpath('//a[contains(@href, "tel:")]/@href').getall())
        item["addr_full"] = sel.xpath('//strong[contains(text(), "Address")]/../text()').getall()
        item["branch"] = item.pop("name")
        for brand_id, brand_details in MOCHACHOS_BRANDS.items():
            if brand_id in location["categories"]:
                item.update(brand_details)
        return item
