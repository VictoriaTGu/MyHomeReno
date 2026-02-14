from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from planner.models import Project, Material, ProjectMaterial


class Command(BaseCommand):
    help = 'Seed the database with sample data'

    def handle(self, *args, **options):
        # Create or get test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created test user'))
        else:
            self.stdout.write('Test user already exists')

        # Create materials
        materials_data = [
            # Copper pipe materials
            {'name': '1/2" copper pipe', 'category': 'pipe', 'unit': 'ft', 'store': 'home_depot'},
            {'name': '3/4" copper pipe', 'category': 'pipe', 'unit': 'ft', 'store': 'lowes'},
            {'name': 'SharkBite 1/2" coupler', 'category': 'fitting', 'unit': 'piece', 'store': 'home_depot'},
            {'name': 'SharkBite 3/4" coupler', 'category': 'fitting', 'unit': 'piece', 'store': 'home_depot'},
            
            # Tools
            {'name': 'Pipe cutter', 'category': 'tool', 'unit': 'piece', 'store': 'home_depot'},
            {'name': 'Adjustable wrench', 'category': 'tool', 'unit': 'piece', 'store': 'lowes'},
            {'name': 'Torch (propane)', 'category': 'tool', 'unit': 'piece', 'store': 'home_depot'},
            
            # Bathroom vanity materials
            {'name': 'Vanity sink 24"', 'category': 'fixture', 'unit': 'piece', 'store': 'lowes'},
            {'name': 'Faucet (chrome)', 'category': 'fixture', 'unit': 'piece', 'store': 'home_depot'},
            {'name': 'P-trap 1-1/4"', 'category': 'plumbing', 'unit': 'piece', 'store': 'lowes'},
            
            # Drywall
            {'name': 'Drywall sheet 4x8', 'category': 'material', 'unit': 'piece', 'store': 'home_depot'},
            {'name': 'Drywall joint compound', 'category': 'material', 'unit': 'bag', 'store': 'lowes'},
            {'name': 'Drywall tape', 'category': 'material', 'unit': 'roll', 'store': 'home_depot'},
        ]

        created_materials = {}
        for mat_data in materials_data:
            material, created = Material.objects.get_or_create(
                name=mat_data['name'],
                category=mat_data['category'],
                unit=mat_data['unit'],
                defaults={'store': mat_data.get('store')}
            )
            created_materials[mat_data['name']] = material
            if created:
                self.stdout.write(f'Created material: {material.name}')

        # Create projects
        projects_data = [
            {
                'name': 'Replace a section of copper pipe',
                'description': 'Replace a leaking section of 1/2" copper pipe with new SharkBite fittings',
                'materials': [
                    ('1/2" copper pipe', 10),  # 10 feet
                    ('SharkBite 1/2" coupler', 2),
                    ('Pipe cutter', 1),
                    ('Adjustable wrench', 1),
                ]
            },
            {
                'name': 'Install new vanity',
                'description': 'Complete bathroom vanity replacement with modern 24" sink',
                'materials': [
                    ('Vanity sink 24"', 1),
                    ('Faucet (chrome)', 1),
                    ('P-trap 1-1/4"', 1),
                    ('Adjustable wrench', 1),
                ]
            },
            {
                'name': 'Repair drywall damage',
                'description': 'Patch and finish drywall damage on a wall',
                'materials': [
                    ('Drywall sheet 4x8', 1),
                    ('Drywall joint compound', 2),  # 2 bags
                    ('Drywall tape', 1),
                ]
            },
        ]

        for proj_data in projects_data:
            project, created = Project.objects.get_or_create(
                name=proj_data['name'],
                defaults={
                    'description': proj_data.get('description'),
                    'img': None
                }
            )
            if created:
                self.stdout.write(f'Created project: {project.name}')

                # Add materials to project
                for material_name, quantity in proj_data['materials']:
                    material = created_materials.get(material_name)
                    if material:
                        ProjectMaterial.objects.get_or_create(
                            project=project,
                            material=material,
                            defaults={'quantity': quantity}
                        )

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully'))
