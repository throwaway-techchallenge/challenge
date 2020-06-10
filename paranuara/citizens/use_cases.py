from typing import Set

from citizens.models import Citizen


def get_common_live_brown_eyed_friends(
        citizen_a: Citizen,
        citizen_b: Citizen
) -> Set[Citizen]:
    """Get common friends of two citizens that are alive and have brown eyes."""

    filter_kwargs = {
        'eye_color__color_name': 'brown',
        'has_died': False
    }

    a_friends = citizen_a.friends.filter(**filter_kwargs)
    b_friends = citizen_b.friends.filter(**filter_kwargs)

    return set(a_friends).intersection(b_friends)
