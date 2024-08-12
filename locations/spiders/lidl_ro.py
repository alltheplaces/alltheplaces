from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlROSpider(VirtualEarthSpider):
    name = "lidl_ro"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "5fa0193e1e0c4496aed1acb4af59f35b"
    dataset_name = "Filialdaten-RO/Filialdaten-RO"
    api_key = "An0oYvlZIU9SiOXJnlxv88zCVWyKYv4Z59Uv77KTalXIp--H9F_cg8vioBxxF5im"
