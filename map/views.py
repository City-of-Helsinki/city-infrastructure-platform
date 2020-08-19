from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def map_view(request):
    return render()
