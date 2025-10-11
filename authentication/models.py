# users/models.py
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames. The manager class defines
    the create_user and create_superuser methods.
    """

    def create_user(
        self,
        email,
        password=None,
        date_of_birth=None,
        phone_number=None,
        agreed_to_Terms=None,
        **extra_fields
    ):
        """
        Create and save a regular user with the given email, date of birth, and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            date_of_birth=date_of_birth,
            phone_number=phone_number,
            agreed_to_Terms=agreed_to_Terms,
            **extra_fields
        )
        user.set_password(password)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_active", False)
        extra_fields.setdefault("is_superuser", False)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email,
        password=None,
        date_of_birth=None,
        phone_number=None,
        agreed_to_Terms=None,
        **extra_fields
    ):
        """
        Create and save a superuser with the given email, date of birth, and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(
            email,
            password,
            date_of_birth,
            phone_number,
            agreed_to_Terms,
            **extra_fields
        )
    
class UserRole(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('lawyer', 'Lawyer'),
        ('advocate', 'Advocate'),
        ('paralegal', 'Paralegal'),
        ('law_student', 'Law Student'),
        ('law_firm', 'Law Firm'),
        ('citizen', 'Citizen'),
    ]
    
    role_name = models.CharField(max_length=255, unique=True, choices=ROLE_CHOICES)
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        related_name='roles',
        verbose_name=_('permissions'),
    )

    def __str__(self):
        return self.get_role_name_display()
    
    def assign_permission(self, permission_codename):
        """Assign a permission to this role."""
        try:
            permission = Permission.objects.get(codename=permission_codename)
            RolePermission.objects.get_or_create(role=self, permission=permission)
            return True
        except Permission.DoesNotExist:
            return False
    
    def remove_permission(self, permission_codename):
        """Remove a permission from this role."""
        try:
            permission = Permission.objects.get(codename=permission_codename)
            RolePermission.objects.filter(role=self, permission=permission).delete()
            return True
        except Permission.DoesNotExist:
            return False
    
    def has_permission(self, permission_codename):
        """Check if this role has a specific permission."""
        return self.permissions.filter(codename=permission_codename).exists()

class RolePermission(models.Model):
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('role', 'permission')
        verbose_name = _('role permission')
        verbose_name_plural = _('role permissions')

    def __str__(self):
        return f"{self.role.get_role_name_display()} - {self.permission.codename}"
    



class PolaUser(AbstractUser):
  
    username = None
    email = models.EmailField(_("email address"), unique=True)
    date_of_birth = models.DateField(verbose_name="Birthday", null=True)
    phone_number = models.CharField(
        max_length=15, verbose_name="Phone Number", null=True
    )
    agreed_to_Terms = models.BooleanField(default=False)
    user_profile_pic = models.ImageField(
        upload_to="profile_pics/", null=True, blank=True
    )
    # user_type = models.CharField(max_length=255, choices=USER_TYPE, default="geust")
    user_role = models.ForeignKey(
        UserRole,   on_delete=models.SET_NULL, null=True, blank=True
    )

    groups = models.ManyToManyField(
        Group,
        verbose_name=_("groups"),
        blank=True,
        help_text=_(
            "The groups this user belongs to. A user will get all permissions "
            "granted to each of their groups."
        ),
        related_name="customuser_set",  # Changed related_name
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_("user permissions"),
        blank=True,
        help_text=_("Specific permissions for this user."),
        related_name="customuser_set",  # Changed related_name
        related_query_name="customuser",
    )
    last_login = models.DateTimeField(
        _("last login"), auto_now=False, null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
        "date_of_birth",
        "phone_number",
        "agreed_to_Terms",
    ]
    phone_is_verified = models.BooleanField(default=False)

    objects = CustomUserManager()

    class Meta:
        unique_together = ("email", "phone_number")
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        if self.email is not None:
            return self.email
        return self.phone_number
        
    def has_role(self, role_name):
        """Check if user has a specific role."""
        return self.user_role and self.user_role.role_name == role_name
    
    def has_permission(self, permission_codename):
        """
        Check if user has a specific permission through their role
        or direct user permissions.
        """
        # Check direct user permissions first
        if self.has_perm(permission_codename):
            return True
            
        # Check role-based permissions
        return (
            self.user_role and 
            self.user_role.has_permission(permission_codename)
        )
    
    def assign_role(self, role_name):
        """Assign a role to the user."""
        try:
            role = UserRole.objects.get(role_name=role_name)
            self.user_role = role
            self.save()
            return True
        except UserRole.DoesNotExist:
            return False

