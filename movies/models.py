from django.db import models
from django.contrib.auth.models import User

class Movie(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='movie_images/')

    def __str__(self):
        return str(self.id) + ' - ' + self.name

class Review(models.Model):
    id = models.AutoField(primary_key=True)
    comment = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # soft-delete / visibility flag — reviews are hidden when False
    is_active = models.BooleanField(default=True)

    def hide(self):
        self.is_active = False
        self.save(update_fields=["is_active"])

class Report(models.Model):
    """A simple report/audit record for inappropriate reviews."""
    id = models.AutoField(primary_key=True)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Report {self.id} on review {self.review_id} by {self.reporter}"


class MoviePetition(models.Model):
    """Model for user petitions to add new movies to the catalog."""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    petitioner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='petitions')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    admin_reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Petition: {self.title} by {self.petitioner.username}"

    def get_vote_count(self):
        """Get the net vote count (upvotes - downvotes)."""
        upvotes = self.votes.filter(vote_type=True).count()
        downvotes = self.votes.filter(vote_type=False).count()
        return upvotes - downvotes

    def get_upvotes(self):
        """Get total upvotes."""
        return self.votes.filter(vote_type=True).count()

    def get_downvotes(self):
        """Get total downvotes."""
        return self.votes.filter(vote_type=False).count()

    class Meta:
        ordering = ['-created_at']


class PetitionVote(models.Model):
    """Model for votes on movie petitions."""
    id = models.AutoField(primary_key=True)
    petition = models.ForeignKey(MoviePetition, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    vote_type = models.BooleanField()  # True for upvote, False for downvote
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        vote_str = "upvote" if self.vote_type else "downvote"
        return f"{self.voter.username} {vote_str} on '{self.petition.title}'"

    class Meta:
        unique_together = ('petition', 'voter')  # Prevent duplicate votes
        indexes = [
            models.Index(fields=['petition', 'vote_type']),
        ]