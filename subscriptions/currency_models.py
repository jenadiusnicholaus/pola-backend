"""
Currency models for multi-currency support
Centralized currency management for all monetary transactions
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Currency(models.Model):
    """
    Master currency table for all monetary values in the system
    
    This centralized approach allows:
    - Easy addition of new currencies
    - Consistent currency formatting across the app
    - Exchange rate management
    - Currency-specific display rules
    """
    code = models.CharField(
        max_length=3, 
        unique=True, 
        primary_key=True,
        help_text="ISO 4217 currency code (e.g., TZS, USD, EUR)"
    )
    name = models.CharField(max_length=50, help_text="Full currency name")
    symbol = models.CharField(max_length=10, help_text="Currency symbol (e.g., TSh, $, €)")
    
    # Exchange rate relative to base currency (TZS)
    exchange_rate_to_tzs = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=Decimal('1.000000'),
        validators=[MinValueValidator(Decimal('0.000001'))],
        help_text="Exchange rate to TZS (1 USD = X TZS)"
    )
    
    # Formatting rules
    decimal_places = models.IntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="Number of decimal places to display"
    )
    symbol_position = models.CharField(
        max_length=10,
        choices=[
            ('before', 'Before amount ($100)'),
            ('after', 'After amount (100 TSh)'),
        ],
        default='before',
        help_text="Where to place currency symbol"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this currency can be used for new transactions"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Default currency for the platform"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_rate_update = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When exchange rate was last updated"
    )
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Currency'
        verbose_name_plural = 'Currencies'
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.symbol})"
    
    def format_amount(self, amount):
        """
        Format amount according to currency rules
        
        Args:
            amount: Decimal or float amount
        
        Returns:
            Formatted string (e.g., "$100.00" or "3000 TSh")
        """
        # Round to appropriate decimal places
        rounded = round(float(amount), self.decimal_places)
        
        # Format with decimal places
        if self.decimal_places == 0:
            formatted_amount = f"{int(rounded):,}"
        else:
            formatted_amount = f"{rounded:,.{self.decimal_places}f}"
        
        # Add symbol in correct position
        if self.symbol_position == 'before':
            return f"{self.symbol}{formatted_amount}"
        else:
            return f"{formatted_amount} {self.symbol}"
    
    def convert_to_tzs(self, amount):
        """Convert amount in this currency to TZS"""
        return Decimal(str(amount)) * self.exchange_rate_to_tzs
    
    def convert_from_tzs(self, tzs_amount):
        """Convert TZS amount to this currency"""
        if self.exchange_rate_to_tzs == 0:
            return Decimal('0')
        return Decimal(str(tzs_amount)) / self.exchange_rate_to_tzs
    
    @classmethod
    def get_default(cls):
        """Get the default currency (TZS)"""
        try:
            return cls.objects.get(is_default=True)
        except cls.DoesNotExist:
            # Fallback to TZS
            return cls.objects.get_or_create(
                code='TZS',
                defaults={
                    'name': 'Tanzanian Shilling',
                    'symbol': 'TSh',
                    'exchange_rate_to_tzs': Decimal('1.0'),
                    'decimal_places': 0,
                    'symbol_position': 'after',
                    'is_active': True,
                    'is_default': True
                }
            )[0]
    
    def save(self, *args, **kwargs):
        """Ensure only one default currency"""
        if self.is_default:
            # Remove default flag from other currencies
            Currency.objects.filter(is_default=True).exclude(code=self.code).update(is_default=False)
        super().save(*args, **kwargs)
