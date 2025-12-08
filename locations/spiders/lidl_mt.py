from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlMTSpider(VirtualEarthSpider):
    name = "lidl_mt"
    item_attributes = LidlGBSpider.item_attributes
    dataset_id = "a360ccf2bf8c442da306b6eb56c638d7"
    dataset_name = "Filialdaten-IT/Filialdaten-IT"
    api_key = "AotMQpa96W8m5_F4ayN9WYBaEQLlxtI3ma8VpOWubmVHTOdZmmKoXjZ8IGLnratj"
    dataset_filter = "CountryRegion eq 'MT'"
