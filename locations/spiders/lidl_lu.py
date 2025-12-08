from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlLUSpider(VirtualEarthSpider):
    name = "lidl_lu"
    item_attributes = LidlGBSpider.item_attributes
    dataset_id = "2be5f76f36e8484e965e84b7ee0cd1b1"
    dataset_name = "Filialdaten-BE/Filialdaten-BE"
    api_key = "AvGfUYinH_I7qdNZWDlXTHHysoytHWqkqZpxHBN9Z0Z0YLQup0u6qZoB8uQXUW_p"
    dataset_filter = "CountryRegion eq 'LU'"
