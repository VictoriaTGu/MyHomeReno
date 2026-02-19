from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Project, Material, ProjectMaterial, ShoppingList, ShoppingListItem, UserMaterial


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'img']


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