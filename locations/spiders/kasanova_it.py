import chompjs
import phonenumbers as pn

from locations.categories import Categories, apply_category
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class KasanovaITSpider(JSONBlobSpider):
    name = "kasanova_it"
    item_attributes = {"brand": "Kasanova", "brand_wikidata": "Q116214505"}
    start_urls = ["https://www.kasanova.com/it/stores"]

    def extract_json(self, response):
        data_raw = response.xpath(
            '//script[@type="text/x-magento-init"][contains(text(), "store-locator-search")]/text()'
        ).get()
        return chompjs.parse_js_object(data_raw)["*"]["Magento_Ui/js/core/app"]["components"]["store-locator-search"][
            "markers"
        ]

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        if location["store_type"] != "Altri":
            item["name"] = location["store_type"]

        item["street_address"] = merge_address_lines(item.pop("street"))
        item["extras"]["addr:province"] = item.pop("state")

        if wa := location["contact_fax"]:
            item["extras"]["contact:whatsapp"] = pn.format_number(
                pn.parse(wa, "IT"), pn.PhoneNumberFormat.INTERNATIONAL
            )
        item["email"] = location["contact_mail"]

        item["opening_hours"] = OpeningHours()
        for day, hours in zip(DAYS_3_LETTERS_FROM_SUNDAY, location["schedule"]["openingHours"]):
            if len(hours) == 0:
                item["opening_hours"].set_closed(day)
            for span in hours:
                item["opening_hours"].add_range(day, span["start_time"], span["end_time"])

        apply_category(Categories.SHOP_HOUSEWARE, item)

        yield item
