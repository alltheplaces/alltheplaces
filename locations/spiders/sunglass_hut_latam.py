from scrapy import Spider
from scrapy.http import FormRequest, Request

from locations.google_url import url_to_coords
from locations.items import Feature
from locations.spiders.sunglass_hut_1 import SUNGLASS_HUT_SHARED_ATTRIBUTES
from locations.user_agents import BROWSER_DEFAULT

LATAM_COUNTRIES = ["cl", "co", "pe"]


class SunglassHutLatamSpider(Spider):
    name = "sunglass_hut_latam"
    item_attributes = SUNGLASS_HUT_SHARED_ATTRIBUTES
    start_urls = [f"https://latam.sunglasshut.com/{cc}/tienda.php" for cc in LATAM_COUNTRIES]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}
    no_refs = True

    def start_requests(self):
        for cc in LATAM_COUNTRIES:
            yield Request(
                url=f"https://latam.sunglasshut.com/{cc}/tienda.php",
                headers={
                    "User-Agent": BROWSER_DEFAULT,
                    "Referer": f"https://latam.sunglasshut.com/{cc}/tienda.html",
                },
                callback=self.get_states,
                meta={"cc": cc},
            )

    def get_states(self, response):
        for option in response.xpath('.//select[@id="state"]/option'):
            state = option.xpath("text()").get()
            state_id = option.xpath("@value").get()
            if state_id == "0":  # Unselectable cities option
                continue
            yield FormRequest(
                url=f"https://latam.sunglasshut.com/{response.meta['cc']}/js_cargarSelect2.php",
                headers={
                    "User-Agent": BROWSER_DEFAULT,
                    "Accept-Language": "en-GB,en;q=0.9",
                },
                formdata={
                    "edo_tienda": state_id,
                    "query": "P",
                },
                callback=self.fetch_stores,
                meta={
                    "cc": response.meta["cc"],
                    "state_id": state_id,
                    "state": state,
                },
            )

    def fetch_stores(self, response):
        if response.json().get("contenido") is None:
            self.crawler.stats.set_value(
                f"atp/{self.name}/no_cities/{response.meta['cc']}/{response.meta['state_id']}", response.meta["state"]
            )
            return
        for city in response.json()["contenido"]:
            yield FormRequest(
                url=f"https://latam.sunglasshut.com/{response.meta['cc']}/js_cargarSelect2.php",
                headers={
                    "User-Agent": BROWSER_DEFAULT,
                    "Accept-Language": "en-GB,en;q=0.9",
                },
                formdata={
                    "edo_tienda": response.meta["state_id"],
                    "id_prov": city.split("|")[0],
                    "query": "D",
                },
                callback=self.parse,
                meta={
                    "cc": response.meta["cc"],
                    "state": response.meta["state"],
                    "city": city,
                },
            )

    def parse(self, response):
        for location in response.json()["contenido"]:
            item = Feature()
            item["branch"] = location.split("|")[0].removeprefix("SGH ")
            item["street_address"] = location.split("|")[1]
            item["lat"], item["lon"] = url_to_coords(location.split("|")[2])
            item["city"] = response.meta["city"].split("|")[1]
            item["country"] = response.meta["cc"]
            yield item
