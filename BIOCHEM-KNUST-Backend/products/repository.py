from products.models import Product, ProductPayment


class ProductRepo:
    model = Product.objects

    @classmethod
    def get_all_products(cls):
        """Fetches all products."""
        return cls.model.all()
    
    @classmethod
    def get_active_products(cls):
        """Fetches only active products for public display."""
        return cls.model.filter(is_active=True)

    @classmethod
    def get_product_by_id(cls, product_id):
        """Fetches a product by its ID."""
        return cls.model.filter(pk=product_id).first()


class ProductPaymentRepository:
    model = ProductPayment.objects

    @classmethod
    def create_payment(cls, transaction, phone, product, reference, customer_name=None, customer_email=None):
        payment = cls.model.create(
            transaction=transaction,
            product=product,
            phone=phone,
            reference=reference,
            customer_name=customer_name,
            customer_email=customer_email,
            payment_successful=True,
        )
        return payment

    # def get_payment_by_id(self, payment_id):
    #     try:
    #         return ProductPayment.objects.get(payment_id=payment_id)
    #     except ProductPayment.DoesNotExist:
    #         return None
    #
