from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Project(models.Model):
    """Represents a DIY project template."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    img = models.CharField(max_length=500, blank=True, null=True)  # URL or file path
    steps = models.JSONField(default=list, blank=True, null=True)  # AI-generated project steps

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Material(models.Model):
    """Represents a generic material or tool that can appear in multiple projects."""
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)  # e.g., "pipe", "fitting", "tool"
    store = models.CharField(max_length=100, blank=True, null=True)  # e.g., "home_depot", "lowes", "amazon"
    sku = models.CharField(max_length=100, blank=True, null=True)  # product SKU (e.g., ASIN for Amazon)
    unit = models.CharField(max_length=50)  # e.g., "piece", "ft", "m"
    notes = models.TextField(blank=True, null=True)

    # Phase 2: Product mapping fields (populated when user selects a product from search)
    product_title = models.CharField(max_length=500, blank=True, null=True)  # product name from store
    product_url = models.URLField(blank=True, null=True)  # direct store product link
    product_image_url = models.URLField(blank=True, null=True)  # primary product image
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # price of the material

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'category', 'unit')

    def __str__(self):
        return f"{self.name} ({self.unit})"


class ProjectMaterial(models.Model):
    """Join table linking projects to default materials."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='materials')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('project', 'material')
        ordering = ['project', 'material']

    def __str__(self):
        return f"{self.project.name} - {self.material.name} ({self.quantity})"


class ShoppingList(models.Model):
    """Represents an actual working list for a user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shopping_lists')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (User: {self.user.username})"


class ShoppingListItem(models.Model):
    """Join table linking materials to specific shopping lists."""
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('shopping_list', 'material')
        ordering = ['shopping_list', 'material']

    def __str__(self):
        return f"{self.shopping_list.name} - {self.material.name}"


class UserMaterial(models.Model):
    """Join table linking users to materials (to save information about which materials the user already has)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='materials')
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('user', 'material')
        ordering = ['user', 'material']

    def __str__(self):
        return f"{self.user.username} - {self.material.name} ({self.quantity})"


class APICallLog(models.Model):
    """Track API calls per user per day for rate limiting."""
    SERVICE_CHOICES = [
        ('serpapi', 'SerpAPI'),
        ('openai', 'OpenAI'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_calls')
    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    call_count = models.PositiveIntegerField(default=1)
    date = models.DateField(auto_now_add=True)  # Reset daily
    timestamp = models.DateTimeField(auto_now=True)  # Last update time
    
    class Meta:
        unique_together = ('user', 'service', 'date')
        ordering = ['-date', 'service']
        verbose_name = 'API Call Log'
        verbose_name_plural = 'API Call Logs'
    
    def __str__(self):
        return f"{self.user.username} - {self.service} ({self.call_count} calls on {self.date})"
    
    @classmethod
    def increment_call_count(cls, user, service):
        """Increment API call count for user and service on today's date."""
        from django.utils import timezone
        today = timezone.now().date()
        
        obj, created = cls.objects.get_or_create(
            user=user,
            service=service,
            date=today,
            defaults={'call_count': 1}
        )
        
        if not created:
            obj.call_count += 1
            obj.save(update_fields=['call_count', 'timestamp'])
        
        return obj
    
    @classmethod
    def get_call_count(cls, user, service):
        """Get today's API call count for user and service."""
        from django.utils import timezone
        today = timezone.now().date()
        
        try:
            obj = cls.objects.get(user=user, service=service, date=today)
            return obj.call_count
        except cls.DoesNotExist:
            return 0
