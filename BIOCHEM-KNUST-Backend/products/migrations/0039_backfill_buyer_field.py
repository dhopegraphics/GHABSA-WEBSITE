# Generated migration to backfill buyer field for existing ProductPayment records

from django.db import migrations


def backfill_buyer_field(apps, schema_editor):
    """
    Backfill the buyer field for existing ProductPayment records.
    For old purchases, buyer = transaction_record.user (who paid)
    """
    ProductPayment = apps.get_model('products', 'ProductPayment')
    
    # Get all ProductPayments where buyer is NULL
    payments_without_buyer = ProductPayment.objects.filter(buyer__isnull=True)
    
    updated_count = 0
    for payment in payments_without_buyer:
        if payment.transaction_record and payment.transaction_record.user:
            payment.buyer = payment.transaction_record.user
            payment.save(update_fields=['buyer'])
            updated_count += 1
    
    print(f"✅ Backfilled buyer field for {updated_count} ProductPayment records")


def reverse_backfill(apps, schema_editor):
    """
    Reverse migration - set buyer back to NULL
    (only for records that were backfilled)
    """
    # We can't reliably reverse this, so we'll just pass
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0038_productpayment_buyer_productpayment_gift_linked_at_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_buyer_field, reverse_backfill),
    ]
