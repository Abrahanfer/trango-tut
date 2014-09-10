#from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def index(request):
    return HttpResponse("Test with rango and gatitos :3 "
    "<a href='/rango/about'>to about</a>")

def about(request):
    return HttpResponse("Rango Says: Here is the about page. "
    "And <a href='/rango'>here</a> the index")
