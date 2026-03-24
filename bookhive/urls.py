from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # 👇 users FIRST
    path('', include('users.urls')),

    # 👇 core AFTER
    path('', include('core.urls')),

    path('books/', include('books.urls')),
    path('clubs/', include('clubs.urls')),
    path('', include('reviews.urls')),
    path('lists/', include('lists.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)