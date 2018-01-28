# -*- coding: utf-8 -*-
#   Erstellt von Roy Ledermüller mit PyCharm Community Edition
#   Erstelldatum:   03.04.2017
#   Projektname:    django
#   Getestet mit Python 3.5

import pytz, datetime

utcTz = pytz.timezone("UTC")
berlinTz = pytz.timezone("Europe/Berlin")

#System saves in UTC -> timestamps are UTC, Wintertime is +1 -> one hour earlier
gntmDates = [
    berlinTz.localize(datetime.datetime(2017, 2, 16, 21, 30, 0)),
    berlinTz.localize(datetime.datetime(2017, 2, 23, 21, 30, 0)),
    berlinTz.localize(datetime.datetime(2017, 3,  2, 21, 30, 0)),
    berlinTz.localize(datetime.datetime(2017, 3,  9, 21, 30, 0)),
    berlinTz.localize(datetime.datetime(2017, 3, 16, 21, 30, 0)),
    berlinTz.localize(datetime.datetime(2017, 3, 23, 20, 15, 0)),
    berlinTz.localize(datetime.datetime(2017, 3, 30, 20, 15, 0)),
    berlinTz.localize(datetime.datetime(2017, 4,  6, 20, 15, 0)),
    berlinTz.localize(datetime.datetime(2017, 4, 13, 20, 15, 0)),
    berlinTz.localize(datetime.datetime(2017, 4, 20, 20, 15, 0)),
    berlinTz.localize(datetime.datetime(2017, 4, 27, 20, 15, 0)),
    berlinTz.localize(datetime.datetime(2017, 5, 4, 20, 15, 0)),
    berlinTz.localize(datetime.datetime(2017, 5,11, 20, 15, 0)),
    berlinTz.localize(datetime.datetime(2017, 5,18, 20, 15, 0)),
    berlinTz.localize(datetime.datetime(2017, 5,25, 20, 15, 0)),
]