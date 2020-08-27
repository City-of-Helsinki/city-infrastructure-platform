from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


@staff_member_required
def map_view(request):
    return render(request, "index.html")
