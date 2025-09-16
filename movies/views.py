from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review, Report
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction

def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()

    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html', {'template_data': template_data})

def show(request, id):
    movie = Movie.objects.get(id=id)
    # only show active reviews
    reviews = Review.objects.filter(movie=movie, is_active=True)

    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    return render(request, 'movies/show.html', {'template_data': template_data})

@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)

    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html', {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('movies.show', id=id)


@login_required
@require_POST
def report_review(request, id, review_id):
    """Allow authenticated users to report a review. The first report hides the review immediately."""
    review = get_object_or_404(Review, id=review_id, movie__id=id)

    # Prevent reporting an already-hidden review
    if not review.is_active:
        return JsonResponse({'status': 'already_hidden'})

    # Prevent duplicate reports by same user
    if Report.objects.filter(review=review, reporter=request.user).exists():
        return JsonResponse({'status': 'already_reported'})

    with transaction.atomic():
        Report.objects.create(review=review, reporter=request.user, reason=request.POST.get('reason', ''))
        # hide immediately on first report
        review.hide()

    return JsonResponse({'status': 'reported_and_hidden'})