from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import FormRequest, Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

BRANDS = {
    "Arimondo": ({"name": "Pam", "brand": "Pam", "brand_wikidata": "Q105615038"}, Categories.SHOP_SUPERMARKET),
    "Pam": ({"name": "Pam", "brand": "Pam", "brand_wikidata": "Q105615038"}, Categories.SHOP_SUPERMARKET),
    "Pam City": ({"name": "Pam City", "brand": "Pam", "brand_wikidata": "Q105615038"}, Categories.SHOP_SUPERMARKET),
    "Pam Local": ({"brand": "Pam Local", "brand_wikidata": "Q105614389"}, Categories.SHOP_CONVENIENCE),
    "Pam Superstore": ({"name": "Pam Superstore", "brand": "Pam", "brand_wikidata": "Q105615038"},),
    "Pam local": ({"brand": "Pam Local", "brand_wikidata": "Q105614389"}, Categories.SHOP_CONVENIENCE),
    "Panorama": ({"name": "Panorama", "brand": "Pam", "brand_wikidata": "Q105615038"}, Categories.SHOP_SUPERMARKET),
    "RETAIL": ({"name": "Pam", "brand": "Pam", "brand_wikidata": "Q105615038"}, Categories.SHOP_SUPERMARKET),
    "pam": ({"name": "Pam", "brand": "Pam", "brand_wikidata": "Q105615038"}, Categories.SHOP_SUPERMARKET),
}


class PamPanoramaITSpider(Spider):
    name = "pam_panorama_it"

    def start_requests(self) -> Iterable[Request]:
        yield FormRequest(
            url="https://coeus.ppapi.it/api/v2_2/post/query?noCache=0&typeUuid=store",
            formdata={
                "limit": "5000",
                "typeUuid": "store",
                "fields[0]": "slug",
                "fields[1]": "name",
                "fields[2]": "description",
                "fields[3]": "uuid",
                "metadatas[0]": "address",
                "metadatas[1]": "latitude",
                "metadatas[2]": "longitude",
                "metadataQueries[latitude][$between][0]": "-90",
                "metadataQueries[latitude][$between][1]": "90",
                "metadataQueries[longitude][$between][0]": "-180",
                "metadataQueries[longitude][$between][1]": "180",
                "geo": "0,0",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["posts"]:
            item = Feature()
            item["ref"] = location["uuid"]
            item["branch"] = location["name"]
            item["website"] = urljoin("https://www.pampanorama.it/punti-vendita/", location["slug"])
            item["street_address"] = location["metadatas"]["address"]
            item["lat"] = location["metadatas"]["latitude"]
            item["lon"] = location["metadatas"]["longitude"]

            if brand := BRANDS.get(location["description"]):
                item.update(brand[0])
                apply_category(brand[1], item)
            else:
                self.logger.error("Unexpected brand: {}".format(location["description"]))

            yield item
