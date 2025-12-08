from locations.hours import DAYS_FR
from locations.spiders.lidl_be import LidlBESpider


class LidlSESpider(LidlBESpider):
    name = "lidl_se"

    dataset_id = "b340d487953044ba8e2b20406ce3fcc6"
    dataset_name = "Filialdaten-SE/Filialdaten-SE"
    api_key = "AiHIKQCACRaaOyOJQjGEGl5uxp7KOTXwae435wJqW3jBo_HLpRWmOVrhOI-eI-Rj"
    days = DAYS_FR
