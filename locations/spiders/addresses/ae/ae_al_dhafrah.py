from locations.storefinders.open_addresses import OpenAddressesSpider


class AeAlDhafrahSpider(OpenAddressesSpider):
    name = "ae_al_dhafrah"
    item_attributes = {
        "city": "Al Dhafra Region",
        "extras": {"addr:city:en": "Al Dhafra Region", "addr:city:ar": "منطقة الظفرة"},
    }
    source = "ae/az/drm-ar"
