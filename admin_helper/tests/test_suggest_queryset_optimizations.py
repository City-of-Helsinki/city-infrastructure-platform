from io import StringIO

import pytest
from django.contrib import admin
from django.core.management import call_command, CommandError
from django.db import models

from admin_helper.decorators import requires_annotation, requires_fields
from admin_helper.management.commands.suggest_queryset_optimizations import AdminQuerySetGenerator


# -----------------------------------------------------------------------------
# 1. Mock Decorators
# -----------------------------------------------------------------------------
def dummy_annotation(qs):
    return qs


# -----------------------------------------------------------------------------
# 2. Mock Models
# -----------------------------------------------------------------------------
class PublisherProfile(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        managed = False


class Publisher(models.Model):
    profile = models.OneToOneField(PublisherProfile, on_delete=models.CASCADE)

    class Meta:
        managed = False


class Author(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        managed = False


class Tag(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        managed = False


class Series(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        managed = False


class MovieAdaptation(models.Model):
    """Contains solely undecorated fields"""

    def get_title(self):
        pass

    def __str__(self):
        pass

    class Meta:
        managed = False


class Book(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)
    series = models.ForeignKey(Series, on_delete=models.CASCADE)
    movie_adaptation = models.ForeignKey(MovieAdaptation, on_delete=models.CASCADE)

    @requires_fields("series")
    def get_series(self):
        pass

    class Meta:
        managed = False


class Chapter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="chapter_set")

    class Meta:
        managed = False


# -----------------------------------------------------------------------------
# 3. Mock Admins utilizing List & Detail view attributes
# -----------------------------------------------------------------------------
class RelationAdmin(admin.ModelAdmin):
    """Tests splitting 1:1, n:1, 1:n, and n:n across list and detail views."""

    list_display = ["author", "get_tags", "get_series"]
    readonly_fields = ["publisher__profile"]
    fieldsets = [(None, {"fields": ["get_chapters"]})]

    @requires_fields("tags")
    def get_tags(self, obj):
        pass

    @requires_fields("chapter_set")
    def get_chapters(self, obj):
        pass


class AnnotationAdmin(admin.ModelAdmin):
    """Tests annotations appearing in the correct view blocks."""

    list_display = ["get_annotated_author"]
    readonly_fields = ["get_annotated_chapters"]

    @requires_annotation(dummy_annotation)
    @requires_fields("author")
    def get_annotated_author(self, obj):
        pass

    @requires_annotation(dummy_annotation)
    @requires_fields("chapter_set")
    def get_annotated_chapters(self, obj):
        pass


class ChapterInline(admin.TabularInline):
    """Tests an InlineModelAdmin."""

    model = Chapter
    readonly_fields = ["book__author", "book__publisher__profile"]


class UndecoratedAdmin(admin.ModelAdmin):
    """Tests warnings about undecorated methods."""

    list_display = ["movie_adaptation__get_title"]
    readonly_fields = ["movie_adaptation"]
    fields = ["get_ratings"]

    def get_ratings(self):
        pass


# -----------------------------------------------------------------------------
# 4. Pytest Helpers & Test Cases
# -----------------------------------------------------------------------------
def generate_code_for(admin_class, model=Book):
    generator = AdminQuerySetGenerator(admin_class=admin_class, model=model)
    return generator.generate()


def assert_in_block(output, view_type, method, expected_fields, unexpected_fields=None):
    """
    Strictly splits the generated code to verify fields are placed in the correct
    view branch (changelist/change) AND the correct method (select/prefetch).
    """
    # 1. Isolate the View block
    if view_type == "inline":
        block = output
    elif view_type == "changelist":
        block = output.split("_changelist'):")[1].split("elif resolver_match")[0]
    elif view_type == "change":
        block = output.split("_change'):")[1]
    else:
        raise ValueError("Invalid view_type")

    # 2. Isolate the Method block
    if f".{method}(" not in block:
        assert (
            not expected_fields
        ), f"Expected {expected_fields} in {method}, but {method} was missing from the {view_type} block."
        return

    method_block = block.split(f".{method}(")[1].split(")")[0]

    # 3. Assertions
    for field in expected_fields:
        assert f'"{field}"' in method_block, f'"{field}" missing from {view_type} {method}. Found: \n{method_block}'

    if unexpected_fields:
        for field in unexpected_fields:
            assert f'"{field}"' not in method_block, f'"{field}" incorrectly found in {view_type} {method}.'


def test_relations_split_by_view():
    out = generate_code_for(RelationAdmin)

    # List View: author (n:1 -> select), series (n:1 -> select, callable), tags (n:n -> prefetch)
    assert_in_block(out, "changelist", "select_related", ["author", "series"], ["tags"])
    assert_in_block(out, "changelist", "prefetch_related", ["tags"], ["author", "series"])

    # Detail View: publisher__profile (1:1 -> select), chapter_set (1:n -> prefetch)
    assert_in_block(out, "change", "select_related", ["publisher", "publisher__profile"], ["chapter_set", "series"])
    assert_in_block(out, "change", "prefetch_related", ["chapter_set"], ["publisher", "publisher__profile", "series"])


def test_annotations_split_by_view():
    out = generate_code_for(AnnotationAdmin)

    # Isolate views for annotation testing
    changelist_block = out.split("_changelist'):")[1].split("elif resolver_match")[0]
    change_block = out.split("_change'):")[1].split("return qs")[0]

    # List View should have the annotation for the author + the select requirement
    assert "dummy_annotation(qs)  # from list_display" in changelist_block
    assert_in_block(out, "changelist", "select_related", ["author"])

    # Detail View should have the annotation for the chapters + the prefetch requirement
    assert "dummy_annotation(qs)  # from readonly_fields" in change_block
    assert_in_block(out, "change", "prefetch_related", ["chapter_set"])


def test_inline_admin_generation():
    out = generate_code_for(ChapterInline, model=Chapter)

    # Inlines shouldn't have resolver_match blocks (they don't split by url view)
    assert "resolver_match" not in out
    assert "_changelist" not in out

    # Inlines process detail variables right at the top level
    assert_in_block(
        out, "inline", "select_related", ["book", "book__author", "book__publisher", "book__publisher__profile"]
    )
    assert_in_block(out, "inline", "prefetch_related", [])


def test_undecorated_method_warnings(capsys):
    generate_code_for(UndecoratedAdmin)

    # Check stderr for missing decorator warnings
    err = capsys.readouterr().err
    assert "'get_title' on MovieAdaptation lacks decorator metadata" in err
    assert "'__str__' on MovieAdaptation lacks decorator metadata" in err
    assert "'get_ratings' on UndecoratedAdmin lacks decorator metadata" in err


# -----------------------------------------------------------------------------
# 5. CLI Integration Tests
# -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_suggest_queryset_optimizations_command_success():
    """
    Tests that the command runs successfully against a built-in Django admin.
    Using django.contrib.auth.admin.GroupAdmin.
    """
    out = StringIO()
    call_command("suggest_queryset_optimizations", "django.contrib.auth.admin.GroupAdmin", stdout=out)
    output = out.getvalue()

    # Check for header and standard structure
    assert "Generated for GroupAdmin" in output
    assert "def get_queryset(self, request):" in output
    assert "qs = super().get_queryset(request)" in output


def test_suggest_queryset_optimizations_command_error():
    """Tests that a CommandError is raised for a non-existent module path."""
    with pytest.raises(CommandError, match="Failed to import"):
        call_command("suggest_queryset_optimizations", "completely.fake.path.BadAdmin")
