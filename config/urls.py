from django.contrib import admin

from django.urls import path, include


urlpatterns = [

    path('admin/', admin.site.urls),

    path('api/accounts/', include('accounts.urls')),
    path('api/problems/', include('problems.urls')),
    path('api/submissions/', include('submissions.urls')),
    path('api/contests/', include('contests.urls')),

]