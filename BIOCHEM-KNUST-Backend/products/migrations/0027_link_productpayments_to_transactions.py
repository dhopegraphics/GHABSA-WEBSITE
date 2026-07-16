# Generated migration to link ProductPayments to Transactions and sync variant_selections

from django.db import migrations


def link_product_payments(apps, schema_editor):
    """
    Link all ProductPayment records to their corresponding Transaction records
    and sync variant_selections from Transaction to ProductPayment
    """
    Transaction = apps.get_model('payments', 'Transaction')
    ProductPayment = apps.get_model('products', 'ProductPayment')
    
    # Track progress
    linked_count = 0
    synced_count = 0
    
    # Fix ProductPayments without transaction_record
    unlinked = ProductPayment.objects.filter(transaction_record__isnull=True)
    
    for pp in unlinked:
        try:
            # Find matching transaction by reference
            transaction = Transaction.objects.get(reference=pp.reference)
            
            # Link them
            pp.transaction_record = transaction
            
            # Copy variant_selections if ProductPayment is empty but Transaction has data
            if not pp.variant_selections and transaction.variant_selections:
                pp.variant_selections = transaction.variant_selections
                synced_count += 1
            
            pp.save()
            linked_count += 1
            
        except Transaction.DoesNotExist:
            # Skip if no matching transaction found
            pass
        except Exception:
            # Skip on any other error
            pass
    
    # Also sync variant_selections for linked ProductPayments that have empty variant_selections
    linked = ProductPayment.objects.filter(
        transaction_record__isnull=False,
        variant_selections=[]
    )
    
    for pp in linked:
        if pp.transaction_record and pp.transaction_record.variant_selections:
            pp.variant_selections = pp.transaction_record.variant_selections
            pp.save()
            synced_count += 1
    
    print(f"\n✅ Migration complete:")
    print(f"   Linked: {linked_count} ProductPayment records")
    print(f"   Synced: {synced_count} variant_selections")


def reverse_migration(apps, schema_editor):
    """
    Reverse is not needed - we don't want to unlink records
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0011_fix_color_images_architecture'),
        ('payments', '0005_add_variant_selections_field'),
    ]

    operations = [
        migrations.RunPython(link_product_payments, reverse_migration),
    ]
