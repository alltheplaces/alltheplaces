from typing import Any, AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class LaPostePostBoxesFRSpider(Spider):
    name = "la_poste_post_boxes_fr"
    item_attributes = {"operator": "La Poste", "operator_wikidata": "Q373724"}
    allowed_domains = ["data.laposte.fr"]
    # Same stock data-fair robots.txt as la_poste_fr, which blocks the JSON API.
    custom_settings = {"ROBOTSTXT_OBEY": False}
    dataset_attributes = {
        "attribution": "required",
        "attribution:name": "La Poste",
        "attribution:website": "https://data.laposte.fr/datasets/laposte-boiterue",
        "license": "Open Database License",
        "license:website": "https://opendatacommons.org/licenses/odbl/1-0/",
        "license:wikidata": "Q1224853",
        "source": "api",
        "use:commercial": "permit",
    }

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://data.laposte.fr/data-fair/api/v1/datasets/laposte-boiterue/lines?size=10000")

    def parse(self, response: Response) -> Iterable[Any]:
        payload = response.json()
        for box in payload["results"]:
            item = Feature()
            item["ref"] = box["co_mup"]
            item["lat"] = box["va_coord_adr_y"]
            item["lon"] = box["va_coord_adr_x"]
            number = box["va_no_voie"] if box["va_no_voie"] != "NULL" else None
            item["street_address"] = " ".join(filter(None, [number, box.get("lb_extension"), box["lb_voie_ext"]]))
            item["postcode"] = box["co_postal"]
            item["city"] = box["lb_com"]
            item["extras"]["ref:INSEE"] = box["co_insee_com"]

            # Times are local wall-clock times despite the +00:00 suffix.
            collection_times = []
            for days, time in (("Mo-Fr", box["hdl_semaine_extra"]), ("Sa", box["hdl_samedi_extra"])):
                if time != "NULL":
                    collection_times.append(f"{days} {time[1:6]}")
            if collection_times:
                item["extras"]["collection_times"] = "; ".join(collection_times)

            apply_category(Categories.POST_BOX, item)
            yield item

        if next_page := payload.get("next"):
            yield Request(next_page)
