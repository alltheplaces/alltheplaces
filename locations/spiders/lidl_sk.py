from locations.hours import DAYS_SK
from locations.spiders.lidl_at import LidlATSpider


class LidlSKSpider(LidlATSpider):
    name = "lidl_sk"

    dataset_id = "018f9e1466694a03b6190cb8ccc19272"
    dataset_name = "Filialdaten-SK/Filialdaten-SK"
    api_key = "AqN50YiXhDtZtWqXZcb7nWvF-4Xc9rg9IXd6YWepqk4WnlmbvD-NV3KHA3A0dOtw"
    days = DAYS_SK
