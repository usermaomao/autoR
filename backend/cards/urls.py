from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'decks', views.DeckViewSet, basename='deck')
router.register(r'cards', views.CardViewSet, basename='card')
router.register(r'review-logs', views.ReviewLogViewSet, basename='reviewlog')

urlpatterns = [
    # 认证相关
    path('auth/register/', views.register_view, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/me/', views.current_user_view, name='current-user'),

    # 复习相关
    path('review/queue/', views.get_review_queue, name='review-queue'),
    path('review/submit/', views.submit_review, name='review-submit'),
    path('review/undo/', views.undo_review, name='review-undo'),

    # 字典查询相关
    path('dict/en/<str:word>/', views.lookup_english, name='lookup-english'),
    path('dict/zh/<str:char>/', views.lookup_hanzi, name='lookup-hanzi'),
    path('dict/zh/infer-pinyin/', views.infer_pinyin, name='infer-pinyin'),

    # ViewSet 路由
    path('', include(router.urls)),
]
