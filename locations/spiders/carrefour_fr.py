import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class CarrefourFrSpider(scrapy.Spider):
    name = "carrefour_fr"
    item_attributes = {"brand": "Carrefour", "brand_wikidata": "Q217599"}
    allowed_domains = ["https://www.carrefour.fr", "api.woosmap.com", "ws.carrefour.fr"]
    key = "woos-26fe76aa-ff24-3255-b25b-e1bde7b7a683"
    start_urls = [
        f"https://api.woosmap.com/project/config?key={key}",
    ]
    headers = {
        "origin": "https://www.carrefour.fr",
    }

    day_range = {
        1: "Mo",
        2: "Tu",
        3: "We",
        4: "Th",
        5: "Fr",
        6: "Sa",
        7: "Su",
    }

    def start_requests(self):
        yield scrapy.Request(
            url=f"https://api.woosmap.com/project/config?key={self.key}",
            method="GET",
            callback=self.parse_store_grid,
            headers=self.headers,
        )

    def parse_store_grid(self, response):
        config_id = str(response.json().get("updated")).split(".", maxsplit=1)[0]

        # Scan the entire France map with zoom level 10.
        for lat in range(491, 545):
            for long in range(340, 382):
                yield scrapy.Request(
                    url=f"https://api.woosmap.com/tiles/10-{str(lat)}-{str(long)}.grid.json?key={self.key}&_={config_id}",
                    method="GET",
                    callback=self.get_store_ids,
                    headers=self.headers,
                )

    def get_store_ids(self, response):
        json_obj = response.json()
        for store in json_obj["data"]:
            store_id = json_obj["data"].get(store)["store_id"]
            yield scrapy.Request(
                url=f"https://api.woosmap.com/stores/{store_id}?key={self.key}",
                method="GET",
                callback=self.parse_store,
                cb_kwargs=dict(store_id=store_id),
                headers=self.headers,
            )

    def parse_store(self, response, store_id):
        json_obi = response.json()
        store_json = json_obi.get("properties")
        address_info = store_json.get("address")
        geo_json = json_obi.get("geometry")
        contact_info = store_json.get("contact")

        opening_hours = OpeningHours()
        store_oh = store_json.get("opening_hours")
        usual_oh = store_oh.get("usual")
        for day_count in usual_oh if usual_oh else []:
            if len(usual_oh.get(day_count)) >= 1:
                dates = usual_oh.get(day_count)[0]
                if dates["start"] != "":
                    opening_hours.add_range(
                        self.day_range.get(int(day_count)),
                        dates["start"],
                        dates["end"],
                    )
        properties = {
            "name": f"Carrefour {store_json.get('user_properties').get('store_name')}",
            "ref": store_id,
            "street_address": address_info.get("lines")[0],
            "city": address_info.get("city"),
            "postcode": address_info.get("zipcode"),
            "country": address_info.get("country_code"),
            "phone": contact_info.get("phone"),
            "website": contact_info.get("website"),
            "opening_hours": opening_hours.as_opening_hours(),
            "lat": geo_json.get("coordinates")[1],
            "lon": geo_json.get("coordinates")[0],
            "extras": {
                "store_type": ",".join(store_json.get("types"))
                if store_json.get("types")
                else "",
            },
        }
        if "CARREFOUR EXPRESS" in properties["extras"]["store_type"]:
            properties["brand"] = "CARREFOUR EXPRESS"
            properties["brand_wikidata"] = "Q2940190"

        yield GeojsonPointItem(**properties)
