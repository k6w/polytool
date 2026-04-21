"""Tests for `pt text`."""

from __future__ import annotations


def test_diff(runner, cli_app, tmp_path) -> None:
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("one\ntwo\nthree\n", encoding="utf-8")
    b.write_text("one\nTWO\nthree\n", encoding="utf-8")
    result = runner.invoke(cli_app, ["text", "diff", str(a), str(b)])
    assert result.exit_code == 0
    assert "-two" in result.stdout
    assert "+TWO" in result.stdout


def test_diff_missing_file(runner, cli_app, tmp_path) -> None:
    a = tmp_path / "exists.txt"
    a.write_text("ok", encoding="utf-8")
    result = runner.invoke(cli_app, ["text", "diff", str(a), str(tmp_path / "nope.txt")])
    assert result.exit_code != 0


def test_wc(runner, cli_app, tmp_path) -> None:
    p = tmp_path / "x.txt"
    p.write_text("hello world\nthis is line two\n", encoding="utf-8")
    result = runner.invoke(cli_app, ["text", "wc", str(p)])
    assert result.exit_code == 0
    assert "lines: 2" in result.stdout
    assert "words: 6" in result.stdout


def test_case_snake(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["text", "case", "snake", "HelloWorld FooBar"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "hello_world_foo_bar"


def test_case_camel(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["text", "case", "camel", "user-id-token"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "userIdToken"


def test_case_pascal(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["text", "case", "pascal", "user_id_token"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "UserIdToken"


def test_case_unknown(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["text", "case", "bogus", "x"])
    assert result.exit_code != 0


def test_slugify(runner, cli_app) -> None:
    result = runner.invoke(cli_app, ["text", "slugify", "Hello, World! Café"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "hello-world-cafe"


def test_md_to_html(runner, cli_app, tmp_path) -> None:
    p = tmp_path / "x.md"
    p.write_text("# Hi\n\n**bold** and `code`.\n", encoding="utf-8")
    result = runner.invoke(cli_app, ["text", "md-to-html", str(p)])
    assert result.exit_code == 0
    assert "<h1>" in result.stdout
    assert "<strong>bold</strong>" in result.stdout
    assert "<code>code</code>" in result.stdout
