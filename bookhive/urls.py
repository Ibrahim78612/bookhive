from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('clubs/', include('clubs.urls')),
    path("", include("core.urls")),
    path("", include("users.urls")),
    path("books/", include("books.urls")),
    path("", include("reviews.urls")),
    path("lists/", include("lists.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
