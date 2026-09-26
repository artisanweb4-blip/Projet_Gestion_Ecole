from django.shortcuts import render

def home(request):  # Ou dashboard(request) selon le nom de votre fonction
    return render(request, 'base.html')