"""
Regenerate tags for a specific style.
This script should be run inside the Django environment.
"""
import os
import sys

# Add Django project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from app.models import Style, Tag, StyleTag

def regenerate_tags_for_style(style_id):
    """Regenerate tags for a style based on its name and captions."""
    try:
        style = Style.objects.prefetch_related('artworks').get(id=style_id)
        print(f"Style: {style.name} (ID={style.id})")

        # Collect caption words
        all_caption_words = []
        artworks = style.artworks.filter(is_valid=True)

        print(f"\nArtworks ({artworks.count()}):")
        for artwork in artworks:
            print(f"  Artwork {artwork.sequence}: '{artwork.caption}'")
            if artwork.caption:
                words = [word.strip().lower() for word in artwork.caption.split(',')]
                all_caption_words.extend([w for w in words if w])

        # Collect unique tag names
        tag_names_set = set()
        tag_names_set.add(style.name.strip().lower())
        tag_names_set.update(all_caption_words)

        unique_tag_names = sorted(list(tag_names_set))

        print(f"\nTags to create ({len(unique_tag_names)}):")
        for tag_name in unique_tag_names:
            print(f"  - {tag_name}")

        # Get existing tags
        existing_count = style.style_tags.count()
        print(f"\nExisting tags: {existing_count}")

        # Create tags
        sequence_start = existing_count
        created = 0

        for idx, tag_name in enumerate(unique_tag_names):
            if not tag_name or len(tag_name) > 100:
                continue

            tag, _ = Tag.objects.get_or_create(name=tag_name)

            if not StyleTag.objects.filter(style=style, tag=tag).exists():
                StyleTag.objects.create(style=style, tag=tag, sequence=sequence_start + idx)
                tag.usage_count += 1
                tag.save(update_fields=['usage_count'])
                created += 1
                print(f"Added: {tag_name}")

        print(f"\nCreated {created} new tag associations")
        print(f"Total tags now: {style.style_tags.count()}")

    except Style.DoesNotExist:
        print(f"Style {style_id} not found")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    style_id = int(sys.argv[1]) if len(sys.argv) > 1 else 19
    regenerate_tags_for_style(style_id)
