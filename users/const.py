# Gender choices for profiles
GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other'),
]

INTEREST_IN_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
    ('E', 'Everyone'),


]

RELATIONSHIP_CHOICES = [
        ('LSR', 'Looking for Short-term Relationship'),
        ('LLR', 'Looking for Long-term Relationship'),
        ('LFR', 'Looking for Friendship'),
        ('LMR', 'Looking to Meet New People'),
        ('NSR', 'Not Sure Yet'),
    ]

BODY_TYPE_CHOICES = [
    ('SL', 'Slim'),
    ('AV', 'Average'),
    ('AT', 'Athletic'),
    ('CF', 'Curvy'),
    ('FF', 'Full Figure'),
    ('MS', 'Muscular'),
    ('OW', 'Overweight'),
    ('UN', 'Underweight'),
    ('OT', 'Other'),
]

COMPLEXION_CHOICES = [
    ('FA', 'Fair'),
    ('LT', 'Light'),
    ('MD', 'Medium'),
    ('TN', 'Tan'),
    ('DR', 'Dark'),
    ('BR', 'Brown'),
    ('OL', 'Olive'),
    ('BK', 'Black'),
    ('OT', 'Other'),
]

DO_YOU_HAVE_PETS_CHOICES = [
    ('Y', 'Yes, I have pets'),
    ('N', 'No, I don’t have pets'),
    ('D', 'I don’t like pets'),
    ('A', 'I would like to have pets one day'),
]

DO_YOU_HAVE_KIDS_CHOICES = [
    ('Y', 'Yes, I have kids'),
    ('N', 'No, I don’t have kids'),
    ('D', 'I don’t like kids'),
    ('A', 'I would like to have kids one day'),
]

SMOKING_CHOICES = [
    ('Y', 'Yes, I smoke'),
    ('N', 'No, I don’t smoke'),
    ('S', 'Sometimes'),
]

DRINKING_CHOICES = [
    ('Y', 'Yes, I drink'),
    ('N', 'No, I don’t drink'),
    ('S', 'Sometimes'),
]

USER_TYPE_CHOICES = [
        ('S', 'Standard'),
        ('P', 'Premium'),
        ('B', 'Business'),
    ]
   # Dietary Preferences

DIETARY_PREFERENCES_CHOICES = [
        ('V', 'Vegetarian'),
        ('VN', 'Vegan'),
        ('GF', 'Gluten-Free'),
        ('DF', 'Dairy-Free'),
        ('P', 'Pescatarian'),
        ('OU', 'Other'),
        ('N', 'None'),
    ]

# Relationship status choices
RELATIONSHIP_STATUS_CHOICES = [
    ('S', 'Single'),
    ('R', 'In a Relationship'),
    ('M', 'Married'),
    ('D', 'Divorced'),
    ('NSR', 'Not Sure Yet'),
]

# New constants for account status
ACCOUNT_STATUS_CHOICES = [
    ('IA', 'Inactive'),
    ('PA', 'Pending Approval'),
    ('A', 'Active'),
    ('S', 'Suspended'),
    ('B', 'Banned'),
    ('D', 'Deactivated'),
]

# Profile visibility options
VISIBILITY_CHOICES = [
    ('VE', 'Visible to Everyone'),
    ('VM', 'Visible to Matches Only'),
    ('PP', 'Private Profile'),
]


# Interest categories for matching
INTEREST_CATEGORIES = [
    ('MUSIC', 'Music'),
    ('MOVIES', 'Movies & TV'),
    ('SPORTS', 'Sports'),
    ('TRAVEL', 'Travel'),
    ('FOOD', 'Food & Dining'),
    ('FITNESS', 'Fitness & Health'),
    ('READING', 'Reading'),
    ('GAMING', 'Gaming'),
    ('ART', 'Art & Culture'),
    ('TECH', 'Technology'),
    ('OUTDOORS', 'Outdoor Activities'),
    ('PETS', 'Pets'),
    ('COOKING', 'Cooking'),
    ('PHOTOGRAPHY', 'Photography'),
    ('FASHION', 'Fashion'),
]

# Verification status choices
VERIFICATION_STATUS_CHOICES = [
    ('UNVERIFIED', 'Not Verified'),
    ('PENDING', 'Verification Pending'),
    ('VERIFIED', 'Verified'),
    ('REJECTED', 'Verification Rejected'),
]


# ONLINE_STATUS =[
#             ('ONLINE', 'Online'),
#             ('AWAY', 'Away'),
#             ('OFFLINE', 'Offline')
#         ], 