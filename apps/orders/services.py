from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.business_days.services import check_ordering_available, generate_next_daily_order_number
from apps.products.models import Product
from apps.inventory.services import record_inventory_transaction
from apps.inventory.models import InventoryTransaction
from .models import Order, OrderItem

@transaction.atomic
def create_order(
    user=None,
    customer_type=Order.CustomerType.STUDENT,
    order_source=Order.OrderSource.MOBILE,
    items_data=None,
    pickup_time=None,
    notes=None,
    discount_amount=0,
    is_paid=False,
    payment_method='CASH',
    order_type=None
):
    if not items_data:
        raise ValidationError("Order must contain at least one product.")

    now = timezone.localtime()
    is_open, msg, b_day = check_ordering_available(now)
    if not is_open:
        raise ValidationError(f"Cannot place order: {msg}")

    max_prep_minutes = 0
    overall_order_type = order_type or Order.OrderType.READY_FOOD

    for item in items_data:
        product_id = item['product_id']
        qty = int(item['quantity'])
        product = Product.objects.select_for_update().get(id=product_id)

        if not product.is_active:
            raise ValidationError(f"Product '{product.name}' is currently unavailable.")

        is_contact = (overall_order_type == Order.OrderType.CONTACT_ORDER or product.food_type == Product.FoodType.CONTACT_ORDER)
        if not is_contact and product.current_stock < qty:
            raise ValidationError(f"Insufficient stock for '{product.name}'. Available: {product.current_stock}, Requested: {qty}.")

        if product.food_type == Product.FoodType.CONTACT_ORDER:
            overall_order_type = Order.OrderType.CONTACT_ORDER
        elif product.food_type == Product.FoodType.MADE_TO_ORDER and overall_order_type != Order.OrderType.CONTACT_ORDER:
            overall_order_type = Order.OrderType.MADE_TO_ORDER

        if product.preparation_time > max_prep_minutes:
            max_prep_minutes = product.preparation_time

    # Pickup time validation for Made-to-Order & Contact Order
    if overall_order_type in [Order.OrderType.MADE_TO_ORDER, Order.OrderType.CONTACT_ORDER] and pickup_time:
        earliest_allowed = now + timedelta(minutes=max_prep_minutes)
        if isinstance(pickup_time, str):
            try:
                parsed_pickup = datetime.fromisoformat(pickup_time)
                if timezone.is_naive(parsed_pickup):
                    parsed_pickup = timezone.make_aware(parsed_pickup)
                pickup_time = parsed_pickup
            except ValueError:
                raise ValidationError("Invalid pickup_time format. Use ISO format datetime.")

        if pickup_time < earliest_allowed:
            mins_needed = max_prep_minutes
            raise ValidationError(
                f"This order requires approximately {mins_needed} minutes to prepare. "
                f"Earliest allowed pickup time is {earliest_allowed.strftime('%I:%M %p')}."
            )

    # Generate daily order sequence (SAEC-001)
    order_number, b_day = generate_next_daily_order_number(now.date())

    initial_status = Order.Status.AWAITING_PAYMENT
    initial_payment_status = Order.PaymentStatus.PENDING
    confirmed_timestamp = None

    if is_paid:
        initial_payment_status = Order.PaymentStatus.PAID
        initial_status = Order.Status.CONFIRMED
        confirmed_timestamp = now
    elif overall_order_type == Order.OrderType.CONTACT_ORDER:
        initial_status = Order.Status.AWAITING_APPROVAL

    discount_dec = Decimal(str(discount_amount))

    order = Order.objects.create(
        order_number=order_number,
        business_day=b_day,
        user=user,
        customer_type=customer_type,
        order_source=order_source,
        order_type=overall_order_type,
        status=initial_status,
        payment_status=initial_payment_status,
        pickup_time=pickup_time,
        confirmed_at=confirmed_timestamp,
        discount_amount=discount_dec,
        notes=notes
    )

    subtotal = Decimal('0.00')

    for item in items_data:
        product = Product.objects.get(id=item['product_id'])
        qty = int(item['quantity'])
        unit_p = product.price
        total_p = unit_p * qty
        subtotal += total_p

        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            unit_price=unit_p,
            quantity=qty,
            total_price=total_p
        )

        if overall_order_type != Order.OrderType.CONTACT_ORDER:
            record_inventory_transaction(
                product_id=product.id,
                transaction_type=InventoryTransaction.TransactionType.SALE,
                quantity=-qty,
                reference_id=order.order_number,
                notes=f"Order #{order.order_number} ({order_source})",
                user=user
            )

    order.subtotal = subtotal
    order.total_amount = max(Decimal('0.00'), subtotal - discount_dec)
    order.save()

    return order

def get_fcfs_queue():
    """
    Returns active confirmed/preparing orders sorted strictly by confirmed_at ASC (First-Come-First-Served).
    Unpaid orders are excluded.
    """
    return Order.objects.filter(
        status__in=[Order.Status.CONFIRMED, Order.Status.PREPARING, Order.Status.READY],
        payment_status=Order.PaymentStatus.PAID
    ).order_by('confirmed_at', 'id')
