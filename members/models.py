from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Import message models
from .models_message import Message, MessageRecipient, Announcement

class ChurchUser(AbstractUser):
    ROLE_CHOICES = [
        ('member', 'Church Member'),
        ('pastor', 'Pastor'),
        ('secretary', 'Church Secretary'),
        ('elder', 'Church Elder'),
        ('deacon', 'Deacon'),
        ('accountant', 'Accountant'),
        ('admin', 'Administrator'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
    ]
    
    MINISTRY_SPECIALIZATION_CHOICES = [
        ('senior_pastor', 'Senior Pastor'),
        ('associate_pastor', 'Associate Pastor'),
        ('youth_pastor', 'Youth Pastor'),
        ('children_pastor', 'Children Pastor'),
        ('worship_pastor', 'Worship Pastor'),
        ('outreach_pastor', 'Outreach Pastor'),
        ('other', 'Other'),
    ]
    
    # Basic member fields
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    membership_date = models.DateField(default=timezone.now)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    is_active_member = models.BooleanField(default=True)
    baptism_date = models.DateField(null=True, blank=True)
    confirmation_date = models.DateField(null=True, blank=True)
    
    # Pastor-specific fields
    pastoral_license = models.CharField(max_length=50, blank=True, help_text="Pastoral license number")
    ordination_date = models.DateField(null=True, blank=True, help_text="Date of ordination")
    ordination_church = models.CharField(max_length=200, blank=True, help_text="Church where ordained")
    years_in_ministry = models.IntegerField(null=True, blank=True, help_text="Years in ministry")
    theology_education = models.CharField(max_length=200, blank=True, help_text="Theological education")
    ministry_specialization = models.CharField(max_length=50, choices=MINISTRY_SPECIALIZATION_CHOICES, blank=True)
    reference_name = models.CharField(max_length=100, blank=True, help_text="Reference name")
    reference_email = models.EmailField(blank=True, help_text="Reference email")
    reference_phone = models.CharField(max_length=20, blank=True, help_text="Reference phone")
    is_verified_pastor = models.BooleanField(default=False, help_text="Pastor verification status")
    pastor_verification_date = models.DateTimeField(null=True, blank=True, help_text="When pastor was verified")
    can_post_member_donations = models.BooleanField(
        default=False,
        help_text="Whether this accountant can enter members' donations.",
    )
    
    class Meta:
        verbose_name = "Church Member"
        verbose_name_plural = "Church Members"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_app_admin(self):
        """Administrator in the church app (role or Django superuser)."""
        return self.role == 'admin' or self.is_superuser
    
    @property
    def age(self):
        if self.date_of_birth:
            return int((timezone.now().date() - self.date_of_birth).days / 365.25)
        return None

class Family(models.Model):
    FAMILY_HEAD_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
    ]
    
    name = models.CharField(max_length=200)
    family_head = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, related_name='headed_families')
    family_head_role = models.CharField(max_length=20, choices=FAMILY_HEAD_CHOICES)
    address = models.TextField()
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Family"
        verbose_name_plural = "Families"
    
    def __str__(self):
        return self.name

class FamilyMember(models.Model):
    RELATIONSHIP_CHOICES = [
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('grandchild', 'Grandchild'),
        ('grandparent', 'Grandparent'),
        ('other', 'Other'),
    ]
    
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='family_members')
    member = models.ForeignKey(ChurchUser, on_delete=models.CASCADE, related_name='family_memberships')
    relationship_to_head = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    is_dependent = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Family Member"
        verbose_name_plural = "Family Members"
        unique_together = ['family', 'member']
    
    def __str__(self):
        return f"{self.member.full_name} - {self.family.name}"

class Ministry(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    leader = models.ForeignKey(ChurchUser, on_delete=models.SET_NULL, null=True, related_name='led_ministries')
    meeting_day = models.CharField(max_length=20, blank=True)
    meeting_time = models.TimeField(null=True, blank=True)
    meeting_location = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Ministry"
        verbose_name_plural = "Ministries"
    
    def __str__(self):
        return self.name

class MinistryMembership(models.Model):
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('leader', 'Leader'),
        ('assistant', 'Assistant'),
    ]
    
    ministry = models.ForeignKey(Ministry, on_delete=models.CASCADE, related_name='memberships')
    member = models.ForeignKey(ChurchUser, on_delete=models.CASCADE, related_name='ministry_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    join_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Ministry Membership"
        verbose_name_plural = "Ministry Memberships"
        unique_together = ['ministry', 'member']
    
    def __str__(self):
        return f"{self.member.full_name} - {self.ministry.name}"


class ChurchGroup(models.Model):
    GROUP_TYPE_CHOICES = [
        ("youth", "Vijana"),
        ("women", "Akina Mama"),
        ("choir", "Kwaya"),
        ("men", "Akina Baba"),
        ("elders", "Wazee"),
        ("children", "Watoto"),
        ("worship", "Ibada / Worship"),
        ("other", "Kundi Lingine"),
    ]

    name = models.CharField(max_length=120, unique=True)
    group_type = models.CharField(max_length=20, choices=GROUP_TYPE_CHOICES)
    description = models.TextField(blank=True)
    leader = models.ForeignKey(
        ChurchUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_church_groups",
        verbose_name="Mwenyekiti wa kundi",
    )
    secretary = models.ForeignKey(
        ChurchUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="secretary_church_groups",
        verbose_name="Katibu wa kundi",
    )
    accountant = models.ForeignKey(
        ChurchUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accountant_church_groups",
        verbose_name="Mhasibu wa kundi",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Church Group"
        verbose_name_plural = "Church Groups"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def display_title(self):
        """Kichwa cha ukurasa: Vijana, Akina Mama, Kwaya, n.k."""
        return self.get_group_type_display()


class GroupMembership(models.Model):
    ROLE_CHOICES = [
        ("leader", "Mwenyekiti"),
        ("assistant", "Msaidizi"),
        ("secretary", "Katibu"),
        ("accountant", "Mhasibu"),
        ("member", "Mwanachama"),
    ]

    group = models.ForeignKey(
        ChurchGroup, on_delete=models.CASCADE, related_name="memberships"
    )
    member = models.ForeignKey(
        ChurchUser, on_delete=models.CASCADE, related_name="group_memberships"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")
    joined_at = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Group Membership"
        verbose_name_plural = "Group Memberships"
        unique_together = ["group", "member"]

    def __str__(self):
        return f"{self.member.full_name} - {self.group.name} ({self.role})"


class GroupActivity(models.Model):
    group = models.ForeignKey(
        ChurchGroup, on_delete=models.CASCADE, related_name="activities"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    activity_date = models.DateField(default=timezone.now)
    created_by = models.ForeignKey(
        ChurchUser, on_delete=models.SET_NULL, null=True, related_name="group_activities"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Group Activity"
        verbose_name_plural = "Group Activities"
        ordering = ["-activity_date", "-created_at"]

    def __str__(self):
        return f"{self.group.name} - {self.title}"


class UniversityStudentRecord(models.Model):
    """Wanafunzi wa chuo — rekodi inabaki hata baada ya kuhitimu."""

    STATUS_CHOICES = [
        ("studying", "Anasoma"),
        ("completed", "Amehitimu"),
        ("paused", "Amesimama"),
    ]

    LEVEL_CHOICES = [
        ("certificate", "Cheti"),
        ("diploma", "Diploma"),
        ("degree", "Shahada (Digrii)"),
        ("masters", "Uzamili"),
        ("phd", "PhD"),
        ("other", "Nyingine"),
    ]

    member = models.ForeignKey(
        ChurchUser,
        on_delete=models.CASCADE,
        related_name="university_records",
    )
    institution = models.CharField(max_length=200, verbose_name="Chuo / Chuo kikuu")
    course = models.CharField(max_length=200, verbose_name="Kozi / Programu")
    faculty = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Ndaki",
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default="degree",
    )
    year_started = models.PositiveIntegerField(null=True, blank=True)
    year_completed = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Mwaka wa kuhitimu (jaza mwanafunzi anapomaliza).",
    )
    expected_completion_year = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="studying",
    )
    notes = models.TextField(blank=True, help_text="Maelezo ya ziada kwa mchungaji.")
    recorded_by = models.ForeignKey(
        ChurchUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="university_records_recorded",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rekodi ya Mwanafunzi wa Chuo"
        verbose_name_plural = "Wanafunzi wa Chuo"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.member.full_name} — {self.course} @ {self.institution}"

    @property
    def is_alumni(self):
        return self.status == "completed"
