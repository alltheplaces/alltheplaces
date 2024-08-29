import chompjs

from locations.hours import DAYS_GR, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class SklavenitisGRSpider(JSONBlobSpider):
    name = "sklavenitis_gr"
    item_attributes = {
        "brand": "Sklavenitis",
        "brand_wikidata": "Q7536037",
    }
    start_urls = ["https://www.sklavenitis.gr/about/katastimata/"]
    # TODO: Technically, doesn't need to be playwright as I can get it to work via url when copying what my browser does
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def extract_json(self, response):
        locations = []
        for json_data in response.xpath("//*[@data-store]/@data-store").getall():
            locations.append(chompjs.parse_js_object(json_data))

        return locations

    def post_process_item(self, item, response, location):
        # {'Key': '1004', 'Title': 'Αγιά', 'Address': 'Supermarket | Αμύρου 8', 'ZipCode': '400 03', 'County': 'Λάρισας', 'Area': 'Αγιά', 'Latitude': 39.7191, 'Longitude': 22.75468, 'DirectionsUrl': 'https://www.google.gr/maps/place/%CE%A3%CE%BF%CF%8D%CF%80%CE%B5%CF%81+%CE%9C%CE%AC%CF%81%CE%BA%CE%B5%CF%84+%C2%AB%CE%91%CE%B3%CE%BF%CF%81%CE%AC%C2%BB/@39.7191011,22.7546833,21z/data=!4m14!1m7!3m6!1s0x14a78460cd0aaa9f:0xb84f5f02ca0c6677!2zzqPOv8-Nz4DOtc-BIM6czqzPgc66zrXPhCDCq86RzrPOv8-BzqzCuw!8m2!3d39.7191264!4d22.7548501!16s%2Fg%2F11f39zdb81!3m5!1s0x14a78460cd0aaa9f:0xb84f5f02ca0c6677!8m2!3d39.7191264!4d22.7548501!16s%2Fg%2F11f39zdb81?hl=el', 'PhoneNumber': "<a href='tel:249 402 3799'>249 402 3799</a>", 'Email': 'g87@sklavenitis.com', 'WorkingHours': 'Δευτέρα - Παρασκευή: 08:00-21:00<br/>Σάββατο: 08:00-20:00', 'Image': 'https://s1.sklavenitis.gr/images/260x115/files/Boreia_Ellada_Stores/G87_ΑΓΙΑ.jpg', 'ParkingSlotsAvailable': None, 'Services': None, 'RecyclingServices': [{'Title': 'Μπαταρίες', 'Icon': 'mpataries', 'Order': 10}]}

        item["ref"] = location["Key"]
        item["image"] = location["Image"]
        item["phone"] = item["phone"].split("tel:")[1].split("'>")[0]
        if " | " in item["addr_full"]:
            store_type, item["addr_full"] = item["addr_full"].split(" | ")
            # TODO: Someone with local knowledge may wish to map more detailed attributes
            if "Supermarket" in store_type:
                pass
            elif "Freshmarket" in store_type:
                # Greengrocer? Farmers Market? Pictures make it look just like a small supermarket.
                pass
            elif "Self Service" in store_type or "Self-service" in store_type:
                # Convenience? Pictures make it look just like a small supermarket.
                pass
            elif "Hypermarket" in store_type:
                pass
            else:
                self.logger.warn("Unknown type: " + store_type)

        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(location["WorkingHours"].replace("<br/>", "; "), DAYS_GR)

        # TODO: Mapping of 'ParkingSlotsAvailable': None, 'Services': None, 'RecyclingServices'

        yield item
