from django.db import transaction
from django.core.exceptions import ValidationError
from apps.products.models import Product
from .models import InventoryTransaction

@transaction.atomic
def record_inventory_transaction(product_id, transaction_type, quantity, reference_id=None, notes=None, user=None):
    """
    Atomically updates product stock and logs an InventoryTransaction.
    Prevents negative stock / overselling.
    """
    product = Product.objects.select_for_update().get(id=product_id)
    prev_stock = product.current_stock
    new_stock = prev_stock + quantity

    if product.food_type != Product.FoodType.CONTACT_ORDER and new_stock < 0:
        raise ValidationError(f"Insufficient stock for {product.name}. Current stock: {prev_stock}, Requested reduction: {abs(quantity)}.")

    product.current_stock = max(0, new_stock) if product.food_type == Product.FoodType.CONTACT_ORDER else new_stock
    product.update_availability_status()

    trx = InventoryTransaction.objects.create(
        product=product,
        transaction_type=transaction_type,
        quantity=quantity,
        previous_stock=prev_stock,
        new_stock=new_stock,
        reference_id=reference_id,
        notes=notes,
        created_by=user
    )
    return trx
