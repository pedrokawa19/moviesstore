from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='movies.index'),
    path('<int:id>/', views.show, name='movies.show'),
    path('<int:id>/review/<int:review_id>/report/', views.report_review, name='movies.report_review'),
    path('<int:id>/review/create/', views.create_review, name='movies.create_review'),
    path('<int:id>/review/<int:review_id>/edit/', views.edit_review, name='movies.edit_review'),
    path('<int:id>/review/<int:review_id>/delete/', views.delete_review, name='movies.delete_review'),
    # Movie Petition URLs
    path('petitions/', views.petition_list, name='movies.petition_list'),
    path('petitions/create/', views.petition_create, name='movies.petition_create'),
    path('petitions/<int:petition_id>/', views.petition_detail, name='movies.petition_detail'),
    path('petitions/<int:petition_id>/vote/', views.petition_vote, name='movies.petition_vote'),
]