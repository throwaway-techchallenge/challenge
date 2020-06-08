from django.db import models
from django.db.models import fields

# Postgres documentation states that enforcing the default 255 character
# limit on character fields is an anti-pattern.
# We're opting for it anyway for two reasons:
# - The only character field in Django that doesn't require specifying
#   max_length is TextField, but that comes with default multi-line form
#   template that we'd have to override everywhere.
# - It reduces the risk when switching between different databases, as we're not
#   sure if Postgres is the one we're going to stick with yet.
# This could potentially be resolved if Django ends up lifting the requirement
# for max_length on all CharField fields.
DEFAULT_CHARFIELD_LENGTH = 255


class Food(models.Model):
    """
    Food liked by Citizens.

    New food types weren't deemed a common enough occurrence to warrant
    a dedicated model. Instead, we explicitly define types as strings to achieve
    relative type-safety.
    """

    FRUIT = 'fruit'
    VEGETABLE = 'vegetable'
    OTHER = 'other'
    FOOD_TYPES = [FRUIT, VEGETABLE, OTHER]

    KNOWN_FRUITS = ['orange', 'apple', 'banana', 'strawberry']
    KNOWN_VEGETABLES = ['beetroot', 'celery', 'carrot', 'cucumber']

    name = fields.CharField(max_length=DEFAULT_CHARFIELD_LENGTH, unique=True)
    type = fields.CharField(
        max_length=DEFAULT_CHARFIELD_LENGTH,
        choices=[(food_type, food_type) for food_type in FOOD_TYPES]
    )


class Company(models.Model):
    """A company existing on Paranuara."""
    name = fields.CharField(max_length=DEFAULT_CHARFIELD_LENGTH)


class EyeColor(models.Model):
    """
    Citizen's eye color representation.

    Given that filtering by eye colour is present in the initial requirements,
    it was deemed important enough to warrant a separate model, so we can
    manage type-safety without having to limit the possible set of colors
    be hard-coding them in the code.
    """
    color_name = fields.CharField(max_length=DEFAULT_CHARFIELD_LENGTH,
                                  unique=True)


class Address(models.Model):
    """
    A Citizen's address.

    All the fields here could potentially be their own models if functionality
    related to addresses is needed. The current implementation is a safe
    middle-ground between fully normalised and purely string-based addresses.
    """

    street_address = fields.CharField(max_length=DEFAULT_CHARFIELD_LENGTH)
    city_name = fields.CharField(max_length=DEFAULT_CHARFIELD_LENGTH)
    state_name = fields.CharField(max_length=DEFAULT_CHARFIELD_LENGTH)
    post_code = fields.CharField(max_length=DEFAULT_CHARFIELD_LENGTH)


class Tag(models.Model):
    """
    A generic tag linked to a Citizen.

    Current tagging implementation supports tagging of citizens only.
    If a more comprehensive tagging system is needed it can be solved by
    e.g. introducing Django's generic foreign keys.
    See: https://docs.djangoproject.com/en/3.0/ref/contrib/contenttypes/#generic-relations"""
    name = fields.CharField(max_length=DEFAULT_CHARFIELD_LENGTH, unique=True)


class Citizen(models.Model):
    """A citizen of Paranuara"""
    class Meta:
        ordering = ('id',)

    _id = fields.CharField(max_length=DEFAULT_CHARFIELD_LENGTH, unique=True)
    guid = fields.CharField(max_length=DEFAULT_CHARFIELD_LENGTH, unique=True)

    registered_at = fields.DateTimeField()

    # Name would ideally be split to first and last name but the current
    # source data does not provide that distinction, and we don't want to
    # naively assume only two parts to the name.
    name = fields.CharField(max_length=DEFAULT_CHARFIELD_LENGTH)
    age = fields.SmallIntegerField()
    has_died = fields.BooleanField()

    # Phone numbers are stored naively as plain strings of the same format
    # as in the source data. This might prove insufficient if we have to
    # support multiple phone number formats, but should do for now.
    phone_number = models.CharField(max_length=DEFAULT_CHARFIELD_LENGTH)
    email = models.EmailField()
    address = models.ForeignKey(to=Address, on_delete=models.PROTECT)

    # Balance is stored in cents in order to avoid any potential floating point
    # errors. A DecimalField() might be used instead.
    balance_in_cents = fields.IntegerField(default=0)
    picture_url = fields.CharField(max_length=DEFAULT_CHARFIELD_LENGTH)
    about = fields.TextField()
    greeting = fields.TextField()

    # Eye colour could be sufficiently represented as a plain CharField,
    # or a CharField limited via the "choices" parameter. See model docstring
    # for details.
    eye_color = models.ForeignKey(to=EyeColor, on_delete=models.PROTECT)

    # In order to ensure type-safety of gender in a relatively simple manner,
    # an implementation following ISO/IEC 5218 has been chosen:
    # https://en.wikipedia.org/wiki/ISO/IEC_5218
    gender_code = models.SmallIntegerField(
        choices=[
            (0, "Not known"),
            (1, "Male"),
            (2, "Female"),
            (9, "Not applicable"),
        ]
    )

    # All citizens in the initial provided resources are employed by a company
    # but that doesn't mean that will always be true. This field is nullable to
    # accommodate potential future unemployed citizens.
    company = models.ForeignKey(to=Company, null=True,
                                on_delete=models.SET_NULL)

    # Although common understanding of "friends" implies a symmetrical relation,
    # the relations present in the initial provided resources are asymmetrical.
    friends = models.ManyToManyField(to="self", symmetrical=False)

    tags = models.ManyToManyField(to=Tag)

    favourite_food = models.ManyToManyField(to=Food)
