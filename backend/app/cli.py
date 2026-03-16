import click

from .extensions import db
from .models import User
from .services.demo_wardrobe_seed import seed_demo_wardrobe_for_user


def register_cli(app):
    @app.cli.command("seed-demo-wardrobe")
    @click.option("--email", default="demo@wardrobe.local", show_default=True)
    @click.option("--password", default="demo12345", show_default=True)
    @click.option("--name", default="Демо пользователь", show_default=True)
    @click.option("--city", default="Москва", show_default=True)
    def seed_demo_wardrobe(email, password, name, city):
        """Создает демо-пользователя и тестовый гардероб для подбора образов."""

        email = email.strip().lower()
        user = User.query.filter_by(email=email).first()
        created = user is None

        if user is None:
            user = User(email=email, name=name, city=city)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        else:
            user.name = name
            user.city = city
            user.set_password(password)
            db.session.commit()

        seed_demo_wardrobe_for_user(user, replace_existing=True)

        click.echo("Тестовый гардероб успешно заполнен.")
        click.echo(f"Пользователь создан: {'да' if created else 'нет'}")
        click.echo(f"Email: {email}")
        click.echo(f"Пароль: {password}")
        click.echo("Добавлено вещей: 17")
