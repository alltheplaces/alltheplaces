from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AnnexxFRSpider(StructuredDataSpider):
    name = "annexx_fr"
    item_attributes = {"brand": "Annexx"}
    start_urls = ["https://www.selfstorage.fr/store/"]
    wanted_types = ["SelfStorage"]
    drop_attributes = {"image", "twitter", "opening_hours"}

    def parse(self, response, **kwargs):
        for href in response.css("a.center-access::attr(href)").getall():
            yield response.follow(href, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        if not item.get("name"):
            return
        item["branch"] = item.pop("name").replace(" - ", " ").removeprefix("Annexx ")
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
