"""
Management command to create dummy data for testing and development.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from app.models import (
    User, Tag, Style, Artwork, Generation,
    Like, Comment, Notification, Follow, Transaction,
    StyleTag
)
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Create dummy data for testing and development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Comment.objects.all().delete()
            Like.objects.all().delete()
            Notification.objects.all().delete()
            Generation.objects.all().delete()
            Artwork.objects.all().delete()
            StyleTag.objects.all().delete()
            Style.objects.all().delete()
            Follow.objects.all().delete()
            Transaction.objects.all().delete()
            Tag.objects.all().delete()
            User.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Existing data cleared'))

        self.stdout.write('Creating dummy data...')

        # 1. Create Users
        self.stdout.write('Creating users...')
        users = []

        # Create artists
        for i in range(1, 6):
            user = User.objects.create(
                username=f'artist{i}',
                email=f'artist{i}@example.com',
                provider='google',
                provider_user_id=f'google_artist_{i}',
                role='artist',
                token_balance=1000 + i * 100,
                profile_image=f'https://i.pravatar.cc/150?img={i}'
            )
            users.append(user)

        # Create regular users
        for i in range(6, 11):
            user = User.objects.create(
                username=f'user{i}',
                email=f'user{i}@example.com',
                provider='google',
                provider_user_id=f'google_user_{i}',
                role='user',
                token_balance=500 + i * 50,
                profile_image=f'https://i.pravatar.cc/150?img={i}'
            )
            users.append(user)

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(users)} users'))

        # 2. Create Tags
        self.stdout.write('Creating tags...')
        tag_names = [
            'watercolor', 'portrait', 'anime', 'realistic', 'abstract',
            'landscape', 'cyberpunk', 'fantasy', 'minimalist', 'vintage',
            'oil-painting', '3d-render', 'sketch', 'cartoon', 'pixel-art'
        ]
        tags = []
        for name in tag_names:
            tag = Tag.objects.create(name=name, usage_count=random.randint(10, 200))
            tags.append(tag)

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(tags)} tags'))

        # 3. Create Styles
        self.stdout.write('Creating styles...')
        style_descriptions = [
            'Beautiful watercolor style with soft gradients',
            'Anime-inspired character portraits',
            'Photorealistic portrait generation',
            'Cyberpunk cityscape aesthetics',
            'Fantasy landscape with magical elements',
            'Minimalist abstract art',
            'Vintage oil painting style',
            '3D rendered character design',
            'Hand-drawn sketch style',
            'Retro pixel art style'
        ]

        styles = []
        artists = [u for u in users if u.role == 'artist']

        for i, artist in enumerate(artists[:10]):
            for j in range(2):  # 2 styles per artist
                style = Style.objects.create(
                    name=f'{artist.username} Style {j+1}',
                    description=style_descriptions[(i*2+j) % len(style_descriptions)],
                    artist=artist,
                    generation_cost_tokens=random.choice([10, 20, 30, 50]),
                    training_status='completed',
                    thumbnail_url=f'https://picsum.photos/seed/style{i*2+j}/400/400',
                    model_path=f'/models/style_{i*2+j}.safetensors',
                    usage_count=random.randint(50, 500),
                    license_type=random.choice(['personal', 'commercial']),
                    is_active=True
                )
                # Add random tags using StyleTag
                style_tags_list = random.sample(tags, k=random.randint(2, 4))
                for seq, tag in enumerate(style_tags_list):
                    StyleTag.objects.create(style=style, tag=tag, sequence=seq)
                styles.append(style)

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(styles)} styles'))

        # 4. Create Artworks for each style
        self.stdout.write('Adding artworks to styles...')
        for style in styles:
            for i in range(4):  # 4 artworks per style
                Artwork.objects.create(
                    style=style,
                    image_url=f'https://picsum.photos/seed/artwork{style.id}_{i}/512/512',
                    is_valid=True
                )
        self.stdout.write(self.style.SUCCESS('✓ Artworks added'))

        # 5. Create Follows
        self.stdout.write('Creating follows...')
        follows_created = 0
        regular_users = [u for u in users if u.role == 'user']
        for user in regular_users:
            # Each user follows 2-3 artists
            followed_artists = random.sample(artists, k=random.randint(2, 3))
            for artist in followed_artists:
                Follow.objects.create(follower=user, following=artist)
                follows_created += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Created {follows_created} follows'))

        # 6. Create Generations
        self.stdout.write('Creating generations...')
        descriptions = [
            'a beautiful sunset over mountains',
            'portrait of a young woman',
            'cyberpunk city at night',
            'magical forest with glowing mushrooms',
            'ancient castle on a cliff',
            'futuristic space station',
            'peaceful zen garden',
            'dragon flying over clouds',
            'underwater coral reef scene',
            'steampunk airship in the sky'
        ]

        generations = []
        for user in users:
            # Each user creates 3-5 generations
            for _ in range(random.randint(3, 5)):
                style = random.choice(styles)
                is_public = random.choice([True, True, False])  # 2/3 chance public
                aspect_ratio = random.choice(['1:1', '2:2', '1:2'])

                generation = Generation.objects.create(
                    user=user,
                    style=style,
                    description=random.choice(descriptions),
                    result_url=f'https://picsum.photos/seed/gen{len(generations)}/512/512',
                    status='completed',
                    is_public=is_public,
                    aspect_ratio=aspect_ratio,
                    consumed_tokens=random.choice([10, 20, 30]),
                    created_at=timezone.now() - timedelta(days=random.randint(0, 30))
                )
                generations.append(generation)

        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(generations)} generations'))

        # 7. Create Likes
        self.stdout.write('Creating likes...')
        public_generations = [g for g in generations if g.is_public]
        likes_created = 0

        for user in users:
            # Each user likes 5-10 random public images
            liked_gens = random.sample(
                public_generations,
                k=min(random.randint(5, 10), len(public_generations))
            )
            for gen in liked_gens:
                Like.objects.create(user=user, generation=gen)
                likes_created += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Created {likes_created} likes'))

        # 8. Create Comments
        self.stdout.write('Creating comments...')
        comment_texts = [
            'Amazing work!',
            'Love the style!',
            'This is beautiful!',
            'Great composition',
            'The colors are stunning',
            'So creative!',
            'Really impressive',
            'This is my favorite',
            'Wow, incredible detail',
            'Perfect execution'
        ]

        comments_created = 0
        for user in users:
            # Each user comments on 3-5 random public images
            commented_gens = random.sample(
                public_generations,
                k=min(random.randint(3, 5), len(public_generations))
            )
            for gen in commented_gens:
                Comment.objects.create(
                    user=user,
                    generation=gen,
                    content=random.choice(comment_texts)
                )
                comments_created += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Created {comments_created} comments'))

        # 9. Create Token Transactions
        self.stdout.write('Creating token transactions...')
        transactions_created = 0

        for user in users:
            # Each user has 2-3 transactions
            for _ in range(random.randint(2, 3)):
                transaction_type = random.choice(['purchase', 'earn', 'generation'])
                if transaction_type == 'purchase':
                    amount = random.choice([100, 500, 1000])
                    memo = f'Token purchase'
                    Transaction.objects.create(
                        receiver=user,
                        amount=amount,
                        transaction_type=transaction_type,
                        memo=memo,
                        status='completed'
                    )
                elif transaction_type == 'earn':
                    amount = random.randint(50, 200)
                    memo = 'Earned from style usage'
                    Transaction.objects.create(
                        receiver=user,
                        amount=amount,
                        transaction_type=transaction_type,
                        memo=memo,
                        status='completed'
                    )
                else:  # generation
                    amount = random.randint(10, 50)
                    memo = 'Used for image generation'
                    # Find a random generation by this user
                    user_gens = [g for g in generations if g.user == user]
                    related_gen = random.choice(user_gens) if user_gens else None
                    Transaction.objects.create(
                        sender=user,
                        amount=amount,
                        transaction_type=transaction_type,
                        memo=memo,
                        related_generation=related_gen,
                        status='completed'
                    )
                transactions_created += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Created {transactions_created} transactions'))

        # 10. Create Notifications
        self.stdout.write('Creating notifications...')
        notifications_created = 0

        for user in users:
            # Each user has 3-5 notifications
            for _ in range(random.randint(3, 5)):
                notif_type = random.choice(['like', 'comment', 'follow'])

                if notif_type == 'like':
                    # Find a generation by this user
                    user_gens = [g for g in generations if g.user == user and g.is_public]
                    if user_gens:
                        gen = random.choice(user_gens)
                        liker = random.choice([u for u in users if u != user])
                        Notification.objects.create(
                            recipient=user,
                            actor=liker,
                            type='like',
                            target_type='generation',
                            target_id=gen.id,
                            metadata={'message': f'{liker.username} liked your image'},
                            is_read=random.choice([True, False])
                        )
                        notifications_created += 1

                elif notif_type == 'comment':
                    user_gens = [g for g in generations if g.user == user and g.is_public]
                    if user_gens:
                        gen = random.choice(user_gens)
                        commenter = random.choice([u for u in users if u != user])
                        Notification.objects.create(
                            recipient=user,
                            actor=commenter,
                            type='comment',
                            target_type='generation',
                            target_id=gen.id,
                            metadata={'message': f'{commenter.username} commented on your image'},
                            is_read=random.choice([True, False])
                        )
                        notifications_created += 1

                elif notif_type == 'follow' and user.role == 'artist':
                    follower = random.choice([u for u in users if u != user])
                    Notification.objects.create(
                        recipient=user,
                        actor=follower,
                        type='follow',
                        target_type='user',
                        target_id=follower.id,
                        metadata={'message': f'{follower.username} started following you'},
                        is_read=random.choice([True, False])
                    )
                    notifications_created += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Created {notifications_created} notifications'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('DUMMY DATA CREATED SUCCESSFULLY!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'Users: {User.objects.count()}')
        self.stdout.write(f'Tags: {Tag.objects.count()}')
        self.stdout.write(f'Styles: {Style.objects.count()}')
        self.stdout.write(f'Artworks: {Artwork.objects.count()}')
        self.stdout.write(f'Generations: {Generation.objects.count()}')
        self.stdout.write(f'Likes: {Like.objects.count()}')
        self.stdout.write(f'Comments: {Comment.objects.count()}')
        self.stdout.write(f'Follows: {Follow.objects.count()}')
        self.stdout.write(f'Transactions: {Transaction.objects.count()}')
        self.stdout.write(f'Notifications: {Notification.objects.count()}')
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('\nYou can now test the frontend with this data!'))
