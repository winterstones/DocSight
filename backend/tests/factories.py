import factory
from django.contrib.auth import get_user_model
from apps.authentication.models import UserProfile, Tag
from apps.search.models import SearchAuditLog

User = get_user_model()


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag
    
    name = factory.Sequence(lambda n: f"tag_{n}")


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user_{n}@example.com")
    role = User.Role.OPERATOR
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password('password123')


class OperatorFactory(UserFactory):
    role = User.Role.OPERATOR


class AdminFactory(UserFactory):
    role = User.Role.ADMIN
    is_superuser = True
    is_staff = True


class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)

    @factory.post_generation
    def allowed_tags(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.allowed_tags.add(tag)


class SearchAuditLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SearchAuditLog
    
    user = factory.SubFactory(UserFactory)
    query = factory.Faker("sentence")
    results_count = factory.Faker("random_int", min=0, max=100)
