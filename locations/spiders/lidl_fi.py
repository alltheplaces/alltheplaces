from locations.hours import DAYS_FI
from locations.spiders.lidl_at import LidlATSpider


class LidlFISpider(LidlATSpider):
    name = "lidl_fi"

    dataset_id = "d5239b243d6b4672810cbd11f82750f5"
    dataset_name = "Filialdaten-FI/Filialdaten-FI"
    api_key = "AhRg1sJKLrhfytyanzu32Io1e7le8W-AZs5Xo88SgdwF33tPSxjVn9h72EpJ7gqD"
    days = DAYS_FI
