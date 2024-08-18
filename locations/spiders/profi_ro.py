import chompjs

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class ProfiROSpider(JSONBlobSpider):
    name = "profi_ro"
    item_attributes = {
        "brand_wikidata": "Q956664",
        "brand": "PROFI",
    }
    allowed_domains = [
        "www.profi.ro",
    ]
    start_urls = ["https://www.profi.ro/magazine/"]

    def extract_json(self, response):
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "const STORE_LOCATIONS =")]/text()').get()
        )

    def post_process_item(self, item, response, location):
        # {'id': 9393, 'title': 'PROFI Gherla Mihai Eminescu', 'image': 'https://www.profi.ro/wp-content/uploads/2021/11/2038-300x225.jpg',
        # 'city': 'Gherla', 'type': {'name': 'PROFI SUPER', 'slug': 'super', 'image_url': 'https://www.profi.ro/wp-content/uploads/2021/12/profi-super-v.svg'},
        # 'nonstop': True, 'coffeecorner': True, 'url': 'profi_2038_Gherla', 'address': 'Str. Mihai Eminescu, Nr. 3',
        # 'latitude': '47.034018', 'longitude': '23.909367', 'phone': '0725205154 / 0799309971', 'fax': '',
        # 'open_mf_s': '00:00:00 AM', 'open_mf_e': '11:59:00 PM', 'open_sat_s': '00:00:00 AM', 'open_sat_e': '11:59:00 PM', 'open_sun_s': '00:00:00 AM',
        # 'open_sun_e': '11:59:00 PM', 'code': '2038', 'inline_featured_image': '0', '_thumbnail_id': '6500', '_edit_lock': '1667370769:12', '_edit_last': '12',
        # 'rs_page_bg_color': '', '_yoast_wpseo_primary_store_type': '64', '_yoast_wpseo_estimated-reading-time-minutes': '0', '_yoast_wpseo_wordproof_timestamp': '',
        # 'labels': ['coffeecorner', 'nonstop']}
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string("Mo-Fr " + location["open_mf_s"] + " " + location["open_mf_e"])
        item["opening_hours"].add_ranges_from_string("Sa " + location["open_sat_s"] + " " + location["open_sat_e"])
        item["opening_hours"].add_ranges_from_string("Su " + location["open_sun_s"] + " " + location["open_sun_e"])

        yield item
