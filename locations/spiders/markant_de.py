import chompjs
from scrapy import Selector

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class MarkantDESpider(JSONBlobSpider):
    name = "markant_de"
    item_attributes = {
        "brand_wikidata": "Q57523365",
        "brand": "Markant",
    }
    allowed_domains = [
        "www.mein-markant.de",
    ]
    start_urls = ["https://www.mein-markant.de/mein-markt/unsere-maerkte"]

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath('//script[contains(text(), "var oMaerkte = ")]/text()').get())

    def post_process_item(self, item, response, location):
        # {'uid': 168, 'name': 'Verbrauchermarkt Höne OHG Rulle', 'marktnamebild': 'Verbrauchermarkt Höne OHG', 'street': 'Parkallee 1', 'zip': '49134',
        # 'city': 'Rulle<br />Tel.: <a href="tel:054077444">05407 / 7444</a>', 'cityRaw': 'Rulle',
        # 'openings': '<p><br /><strong>&Ouml;ffnungszeiten:<br /></strong>Mo &ndash; Sa.: 7:30 &ndash; 20:00<br />So.: 8:00 - 12:30</p>',
        # 'image': 'dummi-markant-rund.jpg', 'markt_type': 'normal',
        # 'link': '/mein-markt/unsere-maerkte?tx_sharpnessmarkt_sharpnessmarktmap%5Baction%5D=index&tx_sharpnessmarkt_sharpnessmarktmap%5Bcontroller%5D=Fetoplogo&tx_sharpnessmarkt_sharpnessmarktmap%5Bmarkt%5D=168&cHash=0ffe120ea87fe959de84721b6397cd3c',
        # 'lat': '52.3367601', 'lon': '8.0589548', 'is_nah_frisch_markt': 0}
        item["ref"] = location["uid"]
        item["city"] = location["cityRaw"]
        item["website"] = "https://www.mein-markant.de/" + location["link"]

        hours = Selector(text=location["openings"]).xpath("text()").get()
        if hours:
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours)

        yield item
