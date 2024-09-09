from scrapy import Selector

from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class LegendsBarbersZASpider(JSONBlobSpider):
    name = "legends_barbers_za"
    item_attributes = {
        "brand": "Legends Barber",
        "brand_wikidata": "Q116895407",
    }
    start_urls = [
        "https://legends-barber.com/wp-admin/admin-ajax.php?action=yith_sl_get_results&context=frontend&filters[radius][]=500"
    ]
    locations_key = "markers"

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        item["website"] = f"https://legends-barber.com/store-locator/{feature['slug']}/"
        sel = Selector(text=feature["pin_modal"])
        item["addr_full"] = merge_address_lines(sel.xpath('//p[@class="store-address"]/text()').getall())
        yield item
