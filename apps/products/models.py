from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    icon_name = models.CharField(max_length=50, default='Utensils')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    class FoodType(models.TextChoices):
        READY_FOOD = 'READY_FOOD', 'Ready Food (Puffs, Snacks, Bottled drinks)'
        MADE_TO_ORDER = 'MADE_TO_ORDER', 'Made to Order (Tea, Coffee, Pizza, Burger)'
        CONTACT_ORDER = 'CONTACT_ORDER', 'Contact & Order (Bulk/Custom/Special Items)'

    class AvailabilityStatus(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        LOW_STOCK = 'LOW_STOCK', 'Low Stock'
        OUT_OF_STOCK = 'OUT_OF_STOCK', 'Out of Stock'
        CONTACT_ORDER = 'CONTACT_ORDER', 'Contact & Order Only'
        PRE_ORDER = 'PRE_ORDER', 'Pre-Order'
        UNAVAILABLE = 'UNAVAILABLE', 'Unavailable'

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    barcode = models.CharField(max_length=100, blank=True, null=True, unique=True)
    sku = models.CharField(max_length=50, blank=True, null=True, unique=True)
    
    food_type = models.CharField(max_length=30, choices=FoodType.choices, default=FoodType.READY_FOOD)
    preparation_time = models.IntegerField(default=5, help_text="Preparation time in minutes")
    minimum_advance_time = models.IntegerField(default=5, help_text="Minimum advance ordering time in minutes")
    
    current_stock = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=5)
    maximum_stock = models.IntegerField(default=100)
    availability_status = models.CharField(max_length=30, choices=AvailabilityStatus.choices, default=AvailabilityStatus.AVAILABLE)
    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=False, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} (₹{self.price}) - {self.food_type}"

    def update_availability_status(self):
        if not self.is_active:
            self.availability_status = self.AvailabilityStatus.UNAVAILABLE
        elif self.food_type == self.FoodType.CONTACT_ORDER:
            self.availability_status = self.AvailabilityStatus.CONTACT_ORDER
        elif self.current_stock <= 0:
            self.availability_status = self.AvailabilityStatus.OUT_OF_STOCK
        elif self.current_stock <= self.minimum_stock:
            self.availability_status = self.AvailabilityStatus.LOW_STOCK
        else:
            self.availability_status = self.AvailabilityStatus.AVAILABLE
        self.save(update_fields=['current_stock', 'availability_status'])
