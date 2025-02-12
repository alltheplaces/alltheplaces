from locations.hours import DAYS_DK
from locations.spiders.lidl_at import LidlATSpider


class LidlDKSpider(LidlATSpider):
    name = "lidl_dk"

    dataset_id = "9ca2963cb5f44aa3b4c241fed29895f8"
    dataset_name = "Filialdaten-DK/Filialdaten-DK"
    api_key = "AsaaAZuUgeIzOb829GUz0a2yjzX0Xw1-OTmjH_27CS5ilYr5v9ylNxg4rQSRhh8Z"
    days = DAYS_DK
