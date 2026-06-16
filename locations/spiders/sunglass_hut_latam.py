"""Spider for Sunglass Hut Latin America stores (Chile, Colombia, Peru).

Closes #6005
"""

import re

from scrapy import FormRequest, Spider

from locations.google_url import url_to_coords
from locations.items import Feature
from locations.spiders.sunglass_hut import SUNGLASS_HUT_SHARED_ATTRIBUTES

COUNTRY_MAP = {
    "cl": "CL",
    "co": "CO",
    "pe": "PE",
}


class SunglassHutLatamSpider(Spider):
    name = "sunglass_hut_latam"
    item_attributes = SUNGLASS_HUT_SHARED_ATTRIBUTES
    requires_proxy = True
    start_urls = [
        "https://latam.sunglasshut.com/cl/tienda.php",
        "https://latam.sunglasshut.com/co/tienda.php",
        "https://latam.sunglasshut.com/pe/tienda.php",
    ]

    def parse(self, response):
        country_code = re.search(r"/([a-z]{2})/tienda\.php", response.url).group(1)
        base_url = f"https://latam.sunglasshut.com/{country_code}"

        for option in response.xpath('//select//option[@value != "0"]'):
            state_id = option.attrib["value"]
            yield FormRequest(
                url=f"{base_url}/js_cargarSelect2.php",
                formdata={"edo_tienda": state_id, "id_prov": "1", "query": "D"},
                callback=self.parse_stores,
                cb_kwargs={"country": COUNTRY_MAP[country_code]},
            )

    def parse_stores(self, response, country):
        data = response.json()
        if data.get("correcto") != 1:
            return
        for entry in data.get("contenido", []):
            parts = entry.split("|")
            if len(parts) < 3:
                continue
            name = parts[0].strip()
            address = parts[1].strip()
            maps_url = parts[2].strip()

            lat, lon = url_to_coords(maps_url)

            item = Feature()
            item["ref"] = name
            item["branch"] = name
            item["addr_full"] = address
            item["lat"] = lat
            item["lon"] = lon
            item["country"] = country
            yield item
