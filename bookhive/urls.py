from django.urls import path, include

urlpatterns = [
    path("", include("core.urls")),
    path("", include("users.urls")),
    path("books/", include("books.urls")),
    path("", include("reviews.urls")),
    path('clubs/', include('clubs.urls')),
]
