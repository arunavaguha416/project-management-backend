from django.core.management.base import BaseCommand
from django.db.models import Count
from time_tracking.models.time_tracking_models import TimeEntry

class Command(BaseCommand):
    help = 'Remove duplicate TimeEntry records based on user and date'

    def handle(self, *args, **options):
        self.stdout.write('Starting duplicate cleanup...')
        
        # Find duplicates
        duplicates = TimeEntry.objects.values('user_id', 'date')\
            .annotate(dup_count=Count('id'))\
            .filter(dup_count__gt=1)
        
        total_duplicates = len(duplicates)
        self.stdout.write(f'Found {total_duplicates} duplicate groups')
        
        if total_duplicates == 0:
            self.stdout.write('No duplicates found!')
            return
        
        # Process each duplicate group
        for i, dup in enumerate(duplicates, 1):
            self.stdout.write(
                f'Processing {i}/{total_duplicates}: User {dup["user_id"]} on {dup["date"]} '
                f'({dup["dup_count"]} records)'
            )
            
            # Get all entries for this user-date combination
            entries = TimeEntry.objects.filter(
                user_id=dup['user_id'], 
                date=dup['date']
            ).order_by('created_at')
            
            # Keep the first entry (earliest created)
            entries_to_keep = entries.first()
            entries_to_delete = entries.exclude(id=entries_to_keep.id)
            
            deleted_count = entries_to_delete.count()
            entries_to_delete.delete()
            
            self.stdout.write(f'  Kept 1 record, deleted {deleted_count} duplicates')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully cleaned all duplicate records!')
        )
