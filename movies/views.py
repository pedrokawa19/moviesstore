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


def petition_detail(request, petition_id):
    """Display detailed view of a single petition."""
    petition = get_object_or_404(MoviePetition, id=petition_id, is_active=True)
    
    # Get user's vote if authenticated
    user_vote = None
    if request.user.is_authenticated:
        vote = petition.votes.filter(voter=request.user).first()
        user_vote = vote.vote_type if vote else None
    
    template_data = {
        'title': f'Petition: {petition.title}',
        'petition': petition,
        'user_vote': user_vote,
        'upvotes': petition.get_upvotes(),
        'downvotes': petition.get_downvotes(),
        'net_votes': petition.get_vote_count()
    }
    return render(request, 'movies/petition_detail.html', {'template_data': template_data})


@login_required
@require_POST
def petition_vote(request, petition_id):
    """Handle AJAX voting on petitions."""
    petition = get_object_or_404(MoviePetition, id=petition_id, is_active=True)
    
    # Prevent voting on own petition
    if petition.petitioner == request.user:
        return JsonResponse({
            'status': 'error',
            'message': 'You cannot vote on your own petition.'
        })
    
    vote_type_str = request.POST.get('vote_type')
    if vote_type_str not in ['true', 'false']:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid vote type.'
        })
    
    vote_type = vote_type_str == 'true'
    
    with transaction.atomic():
        # Get or create vote
        vote, created = PetitionVote.objects.get_or_create(
            petition=petition,
            voter=request.user,
            defaults={'vote_type': vote_type}
        )
        
        current_user_vote = None
        
        if not created:
            # User already voted, update their vote
            if vote.vote_type == vote_type:
                # Same vote - remove it (toggle off)
                vote.delete()
                action = 'removed'
                current_user_vote = None
            else:
                # Different vote - change it
                vote.vote_type = vote_type
                vote.save()
                action = 'changed'
                current_user_vote = vote_type
        else:
            action = 'added'
            current_user_vote = vote_type
    
    # Return updated vote counts
    return JsonResponse({
        'status': 'success',
        'action': action,
        'upvotes': petition.get_upvotes(),
        'downvotes': petition.get_downvotes(),
        'net_votes': petition.get_vote_count(),
        'user_vote': current_user_vote
    })