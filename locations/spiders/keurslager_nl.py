from chompjs import chompjs
from scrapy import FormRequest, Spider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class KeurslagerNLSpider(Spider):
    name = "keurslager_nl"
    item_attributes = {"brand": "Keurslager", "brand_wikidata": "Q114637402"}
    start_urls = ["https://www.keurslager.nl/winkels/"]

    def parse(self, response):
        for location_id in (chompjs.parse_js_object(response.xpath('//*[contains(text(),"FWP_JSON")]/text()').get()))[
            "preload_data"
        ]["settings"]["map"]["locations"]:
            yield FormRequest(
                url="https://www.keurslager.nl/wp/wp-admin/admin-ajax.php",
                cb_kwargs={
                    "id": location_id["post_id"],
                    "lat": location_id["position"]["lat"],
                    "lon": location_id["position"]["lng"],
                },
                formdata={
                    "action": "facetwp_map_marker_content",
                    "facet_name": "map",
                    "post_id": str(location_id["post_id"]),
                },
                callback=self.parse_details,
            )

    def parse_details(self, response, **kwargs):
        item = Feature()
        item["name"] = response.xpath("//h2/text()").get()
        item["street_address"] = response.xpath("//body/text()[1]").get()
        item["addr_full"] = merge_address_lines(
            [response.xpath("//body/text()[1]").get(), response.xpath("//body/text()[2]").get()]
        )
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
        item["email"] = response.xpath('//*[contains(@href,"mailto:")]/text()').get()
        item["website"] = response.xpath("//a[3]/@href").get()
        item["ref"] = kwargs["id"]
        item["lat"] = kwargs["lat"]
        item["lon"] = kwargs["lon"]
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath("//table//tr"):
            day = day_time.xpath(".//td/text()").get()
            if day_time.xpath(".//td[2]/text()").get() in ["gesloten", None]:
                continue
            open_time, close_time = day_time.xpath(".//td[2]/text()").get().split("-")
            item["opening_hours"].add_range(
                day=day.replace(":", ""), open_time=open_time.strip(), close_time=close_time.strip()
            )
        yield item
