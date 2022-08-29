from scrapy import Spider

from locations.items import GeojsonPointItem


class VivacomBGSpider(Spider):
    name = "vivacom_bg"
    item_attributes = {
        "brand": "Vivacom",
        "brand_wikidata": "Q7937522",
        "country": "BG",
    }
    start_urls = ["https://www.vivacom.bg/bg/stores/xhr?method=getJSON"]

    def parse(self, response):
        for store in response.json():

            if "partners" in store["store_img"]:
                continue

            item = GeojsonPointItem()

            item["ref"] = store["store_id"]
            item["lat"], item["lon"] = store["latlng"].split(",")
            item["name"] = store["store_name"]
            item["phone"] = store["store_phone"]
            item["opening_hours"] = (
                store["store_time"]
                .strip()
                .replace("почивен ден", "off")
                .replace("пон.", "Mo")
                .replace("пт.", "Fr")
                .replace("пет.", "Fr")
                .replace("съб.", "Sa")
                .replace("съб", "Sa")
                .replace("нед.", "Su")
                .replace("нд.", "Su")
            )

            item["extras"] = {}
            item["extras"]["type"] = store["store_type"]

            yield item
