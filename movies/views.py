from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review, Report, MoviePetition, PetitionVote
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.db import transaction
from django.db.models import Count

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
        messages.info(request, 'This review is already hidden.')
        return redirect('movies.show', id=id)

    # Prevent duplicate reports by same user
    if Report.objects.filter(review=review, reporter=request.user).exists():
        messages.info(request, 'You have already reported this review.')
        return redirect('movies.show', id=id)

    with transaction.atomic():
        Report.objects.create(review=review, reporter=request.user, reason=request.POST.get('reason', ''))
        # hide immediately on first report
        review.hide()

    messages.success(request, 'Thank you — the review has been reported and removed.')
    return redirect('movies.show', id=id)


# Movie Petition Views

def petition_list(request):
    """Display all active movie petitions ordered by vote count."""
    petitions = MoviePetition.objects.filter(is_active=True).annotate(
        vote_count=Count('votes')
    ).order_by('-vote_count', '-created_at')
    
    # Add vote info for each petition if user is authenticated
    if request.user.is_authenticated:
        for petition in petitions:
            user_vote = petition.votes.filter(voter=request.user).first()
            petition.user_vote = user_vote.vote_type if user_vote else None
    
    template_data = {
        'title': 'Movie Petitions',
        'petitions': petitions
    }
    return render(request, 'movies/petition_list.html', {'template_data': template_data})


@login_required
def petition_create(request):
    """Allow authenticated users to create new movie petitions."""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        
        if title and description:
            # Check if user already has a petition with similar title
            existing = MoviePetition.objects.filter(
                petitioner=request.user,
                title__icontains=title,
                is_active=True
            ).exists()
            
            if existing:
                messages.warning(request, 'You already have a similar petition active.')
                return render(request, 'movies/petition_create.html', {
                    'template_data': {'title': 'Create Movie Petition'},
                    'form_data': {'title': title, 'description': description}
                })
            
            petition = MoviePetition.objects.create(
                title=title,
                description=description,
                petitioner=request.user
            )
            messages.success(request, f'Your petition for "{title}" has been created!')
            return redirect('movies.petition_list')
        else:
            messages.error(request, 'Please provide both a title and description.')
    
    template_data = {'title': 'Create Movie Petition'}
    return render(request, 'movies/petition_create.html', {'template_data': template_data})