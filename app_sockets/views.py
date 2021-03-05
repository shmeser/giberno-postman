import os

from django.shortcuts import render

from backend.enums import Environment


def index(request):
    context = {
        'ws_protocol': 'ws://' if os.getenv('ENVIRONMENT', Environment.LOCAL.value) == Environment.LOCAL.value else
        'wss://'
    }

    return render(request, 'app_sockets/index.html', context=context)
