from scrapy import Selector

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class BrowArt23USSpider(JSONBlobSpider):
    name = "brow_art_23_us"
    item_attributes = {"brand": "Brow Art 23", "brand_wikidata": "Q115675881"}
    start_urls = [
        "https://browart23.com/wp-admin/admin-ajax.php?action=yith_sl_get_results&context=frontend&filters[radius][]=500"
    ]
    requires_proxy = True
    locations_key = "markers"

    def post_process_item(self, item, response, feature):
        item = Feature()
        item["ref"] = feature["id"]
        item["branch"] = feature["name"]
        item["website"] = f"https://browart23.com/store-locator/{feature["slug"]}/"

        sel = Selector(text=feature["pin_modal"])
        item["addr_full"] = merge_address_lines(sel.xpath('//p[@class="store-address"]/text()').getall())
        item["phone"] = sel.xpath('//li[@class="store-phone"]/a/text()').get()

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(
            " ".join(sel.xpath('//div[@class="store-description"]/p/text()').getall())
        )

        yield item
