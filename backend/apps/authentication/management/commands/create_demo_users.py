from django.core.management.base import BaseCommand
from apps.authentication.models import User, UserProfile, Tag
from django.db import transaction

class Command(BaseCommand):
    help = "Creates demo users (1 admin, 2 operators with different tags)"

    def handle(self, *args, **options):
        with transaction.atomic():
            # Create tags
            tag1, _ = Tag.objects.get_or_create(name="ligne-a")
            tag2, _ = Tag.objects.get_or_create(name="ligne-b")
            tag3, _ = Tag.objects.get_or_create(name="secret")
            
            self.stdout.write("Tags created/fetched.")

            # Create Admin
            admin_user, created = User.objects.get_or_create(
                username="admin",
                defaults={
                    "email": "admin@docsight.local",
                    "role": User.Role.ADMIN,
                    "is_staff": True,
                    "is_superuser": True,
                }
            )
            if created:
                admin_user.set_password("admin123")
                admin_user.save()
                UserProfile.objects.create(user=admin_user)
                self.stdout.write(self.style.SUCCESS("Admin user created."))
            else:
                self.stdout.write("Admin user already exists.")

            # Create Operator 1 (ligne-a)
            op1, created = User.objects.get_or_create(
                username="operator_a",
                defaults={
                    "email": "opa@docsight.local",
                    "role": User.Role.OPERATOR,
                }
            )
            if created:
                op1.set_password("operator123")
                op1.save()
                profile1 = UserProfile.objects.create(user=op1)
                profile1.allowed_tags.add(tag1)
                self.stdout.write(self.style.SUCCESS("Operator 1 (ligne-a) created."))
            else:
                self.stdout.write("Operator 1 already exists.")

            # Create Operator 2 (ligne-b)
            op2, created = User.objects.get_or_create(
                username="operator_b",
                defaults={
                    "email": "opb@docsight.local",
                    "role": User.Role.OPERATOR,
                }
            )
            if created:
                op2.set_password("operator123")
                op2.save()
                profile2 = UserProfile.objects.create(user=op2)
                profile2.allowed_tags.add(tag2)
                self.stdout.write(self.style.SUCCESS("Operator 2 (ligne-b) created."))
            else:
                self.stdout.write("Operator 2 already exists.")

        self.stdout.write(self.style.SUCCESS("Demo users setup completed successfully."))
