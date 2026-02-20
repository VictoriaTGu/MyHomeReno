
import logging
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Project, Material, ProjectMaterial, ShoppingList, ShoppingListItem, UserMaterial

logger = logging.getLogger(__name__)



class ProjectMaterialInputSerializer(serializers.Serializer):
    """Serializer for accepting material_id/quantity or material data in bulk add request."""
    # Either existing material_id or new material data
    material_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    # For creating new materials
    name = serializers.CharField(required=False, allow_blank=False)
    category = serializers.CharField(required=False, allow_blank=False)
    unit = serializers.CharField(required=False, allow_blank=False)
    store = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        logger.info("ProjectMaterialInputSerializer.validate called with data: %s", data)
        material_id = data.get('material_id')
        name = data.get('name')
        category = data.get('category')
        unit = data.get('unit')
        # Must have either material_id or name/category/unit for new material
        if not material_id and not (name and category and unit):
            logger.warning("Validation failed: must provide either material_id or name/category/unit for new material. Data: %s", data)
            raise serializers.ValidationError(
                "Either provide 'material_id' for existing material, or 'name', 'category', and 'unit' to create a new material."
            )
        # Cannot provide both
        if material_id and name:
            logger.warning("Validation failed: cannot provide both material_id and name. Data: %s", data)
            raise serializers.ValidationError(
                "Cannot provide both 'material_id' and material creation data. Choose one approach."
            )
        return data

    def validate_material_id(self, value):
        logger.info("Validating material_id: %s", value)
        if value is not None and not Material.objects.filter(id=value).exists():
            logger.warning("Material with id %s does not exist", value)
            raise serializers.ValidationError(f"Material with id {value} does not exist.")
        return value

    def validate_quantity(self, value):
        logger.info("Validating quantity: %s", value)
        if value <= 0:
            logger.warning("Validation failed: quantity must be positive. Value: %s", value)
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class ProjectSerializer(serializers.ModelSerializer):
    materials = ProjectMaterialInputSerializer(many=True, write_only=True)
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'img', 'materials']

    def create(self, validated_data):
        logger.info("ProjectSerializer.create called with validated_data: %s", validated_data)
        materials_data = validated_data.pop('materials', [])
        project = Project.objects.create(**validated_data)
        created_project_materials = []
        for item in materials_data:
            logger.info("Processing material item: %s", item)
            quantity = item['quantity']
            if item.get('material_id'):
                material = Material.objects.get(id=item['material_id'])
                logger.info("Using existing Material id=%s", item['material_id'])
            else:
                material, created = Material.objects.get_or_create(
                    name=item['name'],
                    category=item['category'],
                    unit=item['unit'],
                    defaults={
                        'store': item.get('store'),
                        'notes': item.get('notes')
                    }
                )
                logger.info("Material get_or_create: %s (created=%s)", material, created)
            project_material, created_pm = ProjectMaterial.objects.get_or_create(
                project=project,
                material=material,
                defaults={'quantity': quantity}
            )
            logger.info("ProjectMaterial get_or_create: %s (created=%s)", project_material, created_pm)
            created_project_materials.append(project_material)
        project._created_project_materials = created_project_materials
        logger.info("Project created: %s with materials: %s", project, created_project_materials)
        return project


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = ['id', 'name', 'category', 'store', 'sku', 'unit', 'notes',
                  'product_title', 'product_url', 'product_image_url']


class ProjectMaterialSerializer(serializers.ModelSerializer):
    material = MaterialSerializer(read_only=True)

    class Meta:
        model = ProjectMaterial
        fields = ['id', 'material', 'quantity']


class AddProjectMaterialsSerializer(serializers.Serializer):
    """Serializer for POST request to add multiple materials to a project."""

    def validate_materials(self, value):
        """Ensure at least one material is provided."""
        if not value:
            raise serializers.ValidationError("At least one material must be provided.")
        return value


class ShoppingListItemSerializer(serializers.ModelSerializer):
    material = MaterialSerializer(read_only=True)

    class Meta:
        model = ShoppingListItem
        fields = ['id', 'material', 'quantity']

    def create(self, validated_data):
        """Handle both existing and new materials."""
        shopping_list = self.context['shopping_list']
        material_data = self.context.get('material_data')

        if material_data:
            # Auto-create Material if it doesn't exist
            material, _ = Material.objects.get_or_create(
                name=material_data['name'],
                category=material_data['category'],
                unit=material_data.get('unit', 'piece'),
                defaults={'store': material_data.get('store')}
            )
        else:
            material = validated_data['material']

        # Check if item already exists for this list
        item, created = ShoppingListItem.objects.get_or_create(
            shopping_list=shopping_list,
            material=material,
            defaults={'quantity': validated_data['quantity']}
        )

        if not created:
            item.quantity = validated_data['quantity']
            item.save()

        return item


class ShoppingListSerializer(serializers.ModelSerializer):
    items = ShoppingListItemSerializer(many=True, read_only=True)
    project = ProjectSerializer(read_only=True)

    class Meta:
        model = ShoppingList
        fields = ['id', 'user', 'project', 'name', 'created_at', 'items']
        read_only_fields = ['created_at']


class ShoppingListCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating shopping lists with optional project."""

    # user should be populated from the request, not provided by the client
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ShoppingList
        fields = ['user', 'project', 'name', "id"]

    def create(self, validated_data):
        shopping_list = ShoppingList.objects.create(**validated_data)

        # If project is specified, populate items from ProjectMaterial
        project = validated_data.get('project')
        if project:
            project_materials = ProjectMaterial.objects.filter(project=project)
            for pm in project_materials:
                ShoppingListItem.objects.get_or_create(
                    shopping_list=shopping_list,
                    material=pm.material,
                    defaults={'quantity': pm.quantity}
                )

        return shopping_list


class UserMaterialSerializer(serializers.ModelSerializer):
    material = MaterialSerializer(read_only=True)

    class Meta:
        model = UserMaterial
        fields = ['id', 'material', 'quantity']

    def create(self, validated_data):
        """Handle creation of user material inventory."""
        user = self.context['user']
        material_data = self.context.get('material_data')

        if material_data:
            # If material_data is provided, use it to get or create material
            material, _ = Material.objects.get_or_create(
                name=material_data['name'],
                category=material_data['category'],
                unit=material_data.get('unit', 'piece'),
                defaults={'store': material_data.get('store')}
            )
        else:
            material = validated_data['material']

        user_material, created = UserMaterial.objects.get_or_create(
            user=user,
            material=material,
            defaults={'quantity': validated_data['quantity']}
        )

        return user_material


class ProductResultSerializer(serializers.Serializer):
    """Serializer for store search product results.

    This represents a normalized product from an external store API.
    Read-only; used only for returning search results.
    """
    name = serializers.CharField()
    description = serializers.CharField()
    price = serializers.FloatField()
    currency = serializers.CharField()
    sku = serializers.CharField()
    url = serializers.URLField()
    image_url = serializers.URLField()
    store = serializers.CharField()

class PlanRequestSerializer(serializers.Serializer):
    """Serializer for validating plan generation requests."""
    description = serializers.CharField(
        max_length=2000,
        min_length=10,
        help_text="Free-form description of the project (10-2000 characters)"
    )


class PlanMaterialSerializer(serializers.Serializer):
    """Serializer for individual materials in a plan."""
    name = serializers.CharField()
    quantity = serializers.FloatField()
    unit = serializers.CharField()
    category = serializers.CharField()


class PlanToolSerializer(serializers.Serializer):
    """Serializer for individual tools in a plan."""
    name = serializers.CharField()
    quantity = serializers.FloatField()
    unit = serializers.CharField()
    category = serializers.CharField()


class PlanResponseSerializer(serializers.Serializer):
    """Serializer for structured plan generation response."""
    materials = PlanMaterialSerializer(many=True)
    tools = PlanToolSerializer(many=True)
    steps = serializers.ListField(child=serializers.CharField())
    warnings = serializers.ListField(child=serializers.CharField())