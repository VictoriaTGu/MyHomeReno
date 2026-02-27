import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Prepare frontend files for deployment'

    def handle(self, *args, **options):
        # Create templates directory
        templates_dir = os.path.join(settings.BASE_DIR, 'templates')
        os.makedirs(templates_dir, exist_ok=True)
        
        # Copy index.html from frontend_build
        frontend_index = os.path.join(settings.BASE_DIR.parent, 'mybackend', 'frontend_build', 'index.html')
        template_index = os.path.join(templates_dir, 'index.html')
        
        if os.path.exists(frontend_index):
            shutil.copy(frontend_index, template_index)
            self.stdout.write(self.style.SUCCESS(f'✓ Copied {frontend_index} to {template_index}'))
        else:
            self.stdout.write(self.style.ERROR(f'✗ Frontend index.html not found at {frontend_index}'))
            return
        
        # Verify the copy
        if os.path.exists(template_index):
            self.stdout.write(self.style.SUCCESS('✓ Verification: index.html exists in templates directory'))
        else:
            self.stdout.write(self.style.ERROR('✗ Verification failed: index.html not found in templates'))
