import chompjs

from locations.categories import Categories, apply_category
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class NuvolariITSpider(JSONBlobSpider):
    name = "nuvolari_it"
    item_attributes = {"brand": "Nuvolari", "brand_wikidata": "Q130702590"}
    start_urls = ["https://www.nuvolari.biz/stores"]

    def extract_json(self, response):
        data_raw = response.xpath(
            '//script[@type="text/x-magento-init"][contains(text(), "store-locator-search")]/text()'
        ).get()
        return chompjs.parse_js_object(data_raw)["*"]["Magento_Ui/js/core/app"]["components"]["store-locator-search"][
            "markers"
        ]

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["street_address"] = merge_address_lines(item.pop("street"))
        item["country"] = "IT"
        if item.get("postcode"):
            item["postcode"] = item["postcode"].strip()

        item["opening_hours"] = OpeningHours()
        for day, hours in zip(DAYS_3_LETTERS_FROM_SUNDAY, location["schedule"]["openingHours"]):
            if len(hours) == 0:
                item["opening_hours"].set_closed(day)
            for span in hours:
                item["opening_hours"].add_range(day, span["start_time"], span["end_time"])

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
