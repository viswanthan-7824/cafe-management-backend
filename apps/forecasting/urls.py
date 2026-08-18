from django.urls import path
from .views import DemandForecastingView

urlpatterns = [
    path('predict/', DemandForecastingView.as_view(), name='forecasting_predict'),
]
