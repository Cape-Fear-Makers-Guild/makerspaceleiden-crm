from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from django.utils import timezone

from selfservice.aggregator_adapter import get_aggregator_adapter

import logging
import datetime
from dateutil import parser
import re
import requests

logger = logging.getLogger(__name__)

# No access restrictions
def index(request):
    aggregator_adapter = get_aggregator_adapter()
    if not aggregator_adapter:
        return HttpResponse(
            "No aggregator configuration found", status=500, content_type="text/plain"
        )

    state = aggregator_adapter.fetch_state_space()
    context = {"open": "false"}

    if state["lights_on"]:
        context = {"open": "true"}  # must be lowercase

    for e in state["machines"]:
        m = e["machine"]
        if "light" in m["name"].lower() and "state" in m and "on" in m["state"].lower():
            context = {"open": "true"}  # must be lowercase

    # {'machine': {'location_name': 'Main room', 'machine_id': 50, 'name': 'Main room lights'}, 'state': 'lights_off'},
    if bool(state["users_in_space"]):
        lst = datetime.datetime(1970, 1, 1)
        for user in state["users_in_space"]:
            ulst = parser.parse(user["ts_checkin"])
            if ulst > lst:
                lst = ulst
        context["lastSinceEpoch"] = lst.strftime("%s")

    return render(request, "spaceapi.json", context)
