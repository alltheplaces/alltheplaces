import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.licenses import Licenses

PARKING_TYPE_MAP = {
    "PARKERINGSHUS": "multi-storey",
    "LANGS_KJOREBANE": "lane",
    "AVGRENSET_OMRADE": "surface",
    "IKKE_VALGT": None,
}


class StatensVegvesenParkingNOSpider(scrapy.Spider):
    """
    Spider for the Norwegian Public Roads Administration (Statens vegvesen)
    parking registration API (Parkeringsregisteret).

    This API provides data about registered parking areas in Norway.
    Documentation: https://parkreg-open.atlas.vegvesen.no/swagger-ui/index.html
    """

    name = "statens_vegvesen_parking_no"
    allowed_domains = ["parkreg-open.atlas.vegvesen.no"]
    start_urls = [
        "https://parkreg-open.atlas.vegvesen.no/ws/no/vegvesen/veg/parkeringsomraade/parkeringsregisteret/v1/parkeringsomraade?datafelter=alle"
    ]
    dataset_attributes = Licenses.NO_NLODv2.value | {
        "attribution:name": "Contains data under the Norwegian licence for Open Government data (NLOD) distributed by Statens vegvesen"
    }
    custom_settings = {"DOWNLOAD_TIMEOUT": 120}

    def parse(self, response):
        for parking_area in response.json():
            # Skip deactivated parking areas
            if parking_area.get("deaktivert"):
                continue

            active_version = parking_area.get("aktivVersjon")
            if not active_version:
                continue

            item = DictParser.parse(parking_area)

            # Identifiers
            item["ref"] = str(parking_area.get("id"))
            item["name"] = active_version.get("navn")

            # Address
            item["street_address"] = active_version.get("adresse")
            item["postcode"] = active_version.get("postnummer")
            item["city"] = active_version.get("poststed")

            # Operator / parking provider
            item["operator"] = parking_area.get("parkeringstilbyderNavn")

            # Capacity information
            paid_spaces = active_version.get("antallAvgiftsbelagtePlasser") or 0
            free_spaces = active_version.get("antallAvgiftsfriePlasser") or 0
            total_capacity = paid_spaces + free_spaces
            if total_capacity > 0:
                item["extras"]["capacity"] = str(total_capacity)

            # Disabled parking spaces
            disabled_spaces = active_version.get("antallForflytningshemmede")
            if disabled_spaces and disabled_spaces > 0:
                item["extras"]["capacity:disabled"] = str(disabled_spaces)

            # EV charging spaces
            charging_spaces = active_version.get("antallLadeplasser")
            if charging_spaces and charging_spaces > 0:
                item["extras"]["capacity:charging"] = str(charging_spaces)

            # Fee information
            apply_yes_no(Extras.FEE, item, paid_spaces > 0)

            # Parking type
            parking_type = active_version.get("typeParkeringsomrade")
            if parking_type and parking_type in PARKING_TYPE_MAP:
                osm_parking_type = PARKING_TYPE_MAP[parking_type]
                if osm_parking_type:
                    item["extras"]["parking"] = osm_parking_type

            # Park and ride availability
            apply_yes_no("park_ride", item, active_version.get("innfartsparkering") == "JA")

            apply_category(Categories.PARKING, item)

            yield item
