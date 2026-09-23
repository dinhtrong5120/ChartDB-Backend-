from django.urls import path

from .views import SourceDatabaseIntrospectionView

urlpatterns = [
    path("source-database/introspect", SourceDatabaseIntrospectionView.as_view(), name="source-introspect"),
]

