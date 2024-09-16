from locations.hours import DAYS_FR
from locations.spiders.lidl_be import LidlBESpider


class LidlFRSpider(LidlBESpider):
    name = "lidl_fr"

    dataset_id = "717c7792c09a4aa4a53bb789c6bb94ee"
    dataset_name = "Filialdaten-FR/Filialdaten-FR"
    api_key = "AgC167Ojch2BCIEvqkvyrhl-yLiZLv6nCK_p0K1wyilYx4lcOnTjm6ud60JnqQAa"
    days = DAYS_FR
