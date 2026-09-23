from django.urls import path

from .views import DiagramDetailView, DiagramListCreateView

urlpatterns = [
    path("diagrams", DiagramListCreateView.as_view(), name="diagram-list"),
    path("diagrams/<str:diagram_id>", DiagramDetailView.as_view(), name="diagram-detail"),
]

