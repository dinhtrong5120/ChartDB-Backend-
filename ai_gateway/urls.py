from django.urls import path

from .views import SQLExportStreamView

urlpatterns = [
    path("ai/sql-export/stream", SQLExportStreamView.as_view(), name="ai-sql-export"),
]

