from rest_framework.routers import DefaultRouter # type: ignore
from .views import GestoViewSet

router = DefaultRouter()
router.register(r'gestos', GestoViewSet, basename='gesto')

urlpatterns = router.urls
