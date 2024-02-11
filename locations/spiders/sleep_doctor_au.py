from chompjs import parse_js_object
from scrapy import Selector, Spider

from locations.dict_parser import DictParser


class SleepDoctorAUSpider(Spider):
    name = "sleep_doctor_au"
    item_attributes = {
        "brand": "Sleep Doctor",
        "brand_wikidata": "Q122435030",
        "extras": {
            "shop": "bed",
        },
    }
    allowed_domains = ["sleepdoctor.com.au"]
    start_urls = ["https://sleepdoctor.com.au/apps/store-locator/"]

    def parse(self, response):
        markers = {}

        website_links = response.xpath('//div[@id="addresses_list"]/ul/li')
        for website_link in website_links:
            store_name = website_link.xpath('.//h3[@class="name"]/text()').get()
            website_uri = website_link.xpath('.//div[@class="store_website"]/a/@href').get()
            markers[store_name] = {"website": website_uri}

        js_blob = response.xpath('//script[contains(text(), "markersCoords.push(")]/text()').get()
        markers_js = list(map(lambda x: x.split(");")[0], js_blob.split("markersCoords.push(")[1:]))[:-2]
        for marker_js in markers_js:
            marker_dict = parse_js_object(marker_js)
            address_html = Selector(text=marker_dict["address"])
            marker_dict["name"] = address_html.xpath('//h3[@class="name"]/text()').get()
            marker_dict["street_address"] = address_html.xpath('//span[@class="address"]/text()').get()
            marker_dict["city"] = address_html.xpath('//span[@class="city"]/text()').get()
            marker_dict["state"] = address_html.xpath('//span[@class="prov_state"]/text()').get()
            marker_dict["postcode"] = address_html.xpath('//span[@class="postal_zip"]/text()').get()
            marker_dict.pop("address", None)
            # Fix typo in coordinates for a store
            if marker_dict.get("lng") and "510." in marker_dict["lng"]:
                marker_dict["lng"] = marker_dict["lng"].replace("510.", "150.")
            markers[marker_dict["name"]].update(marker_dict)

        for marker in markers.values():
            item = DictParser.parse(marker)
            if item.get("website"):
                item["website"] = item["website"].replace("http://", "https://")
            yield item
