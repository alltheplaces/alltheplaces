from scrapy.http import FormRequest

from locations.storefinders.store_locator_plus_self import StoreLocatorPlusSelfSpider


class WienerschnitzelUSECSpider(StoreLocatorPlusSelfSpider):
    name = "wienerschnitzel_us_ec"
    item_attributes = {
        "brand_wikidata": "Q324679",
        "brand": "Wienerschnitzel",
    }
    allowed_domains = ["www.wienerschnitzel.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    max_results = 10000
    search_radius = 30000

    def start_requests(self):
        url = f"https://{self.allowed_domains[0]}/wp-admin/admin-ajax.php"
        formdata = {
            "action": "csl_ajax_onload",
            "lat": "0",
            "lng": "0",
            "radius": str(self.search_radius),
            "options[initial_results_returned]": str(self.max_results),
            "options[distance_unit]": "kilometers",
        }
        yield FormRequest(url=url, formdata=formdata, method="POST")

    def parse_item(self, item, location, **kwargs):
        item["branch"] = item.pop("name")
        yield item
