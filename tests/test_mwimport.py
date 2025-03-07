import pytest
from miraheze.mediawiki import mwimport

def test_parse_args_xml_images():
    args = mwimport.parse_args([
        "--xml=dump.xml",
        "--images=images",
        "--images-comment=Importing from https://example.com",
        "examplewiki",
    ], False)
    assert args.xml == "dump.xml"
    assert args.images == "images"
    assert args.images_comment == "Importing from https://example.com"
    assert args.wiki == "examplewiki"

def test_parse_args_images_recursively():
    args = mwimport.parse_args([
        "--images=images",
        "--search-recursively",
        "--images-comment=Importing from https://example.com",
        "examplewiki",
    ], False)
    assert args.images == "images"
    assert args.search_recursively
    assert args.images_comment == "Importing from https://example.com"
    assert args.wiki == "examplewiki"

def test_parse_args_no_log_and_confirm_and_version():
    args = mwimport.parse_args([
        "--no-log",
        "--confirm",
        "--version=0.42",
        "--xml=dump.xml",
        "examplewiki",
    ], False)
    assert args.nolog
    assert args.confirm
    assert args.version == "0.42"

def test_parse_args_username_prefix():
    args = mwimport.parse_args([
        "--xml=dump.xml",
        "--username-prefix=w",
        "examplewiki",
    ], False)
    assert args.username_prefix == "w"

def test_parse_args_need_xml_or_images():
    with pytest.raises(ValueError) as excinfo:
        mwimport.parse_args([
            "examplewiki",
        ])
    assert str(excinfo.value) == "--xml and/or --images must be passed"

def test_parse_args_images_need_comment():
    with pytest.raises(ValueError) as excinfo:
        mwimport.parse_args([
            "--images=images",
            "examplewiki",
        ])
    assert str(excinfo.value) == "--images-comment must be passed when importing images"

def test_parse_args_missing_xml():
    with pytest.raises(ValueError) as excinfo:
        mwimport.parse_args([
            "--xml=/dev/no xml?",
            "examplewiki",
        ])
    assert str(excinfo.value) == "Cannot find XML to import: '/dev/no xml?'"

def test_parse_args_missing_images():
    with pytest.raises(ValueError) as excinfo:
        mwimport.parse_args([
            "--images=/dev/no images?",
            "--images-comment=Importing from https://example.com",
            "examplewiki",
        ])
    assert str(excinfo.value) == "Cannot find images to import: '/dev/no images?'"

def test_get_scripts_xml_images():
    args = mwimport.parse_args([
        "--xml=dump.xml",
        "--images=images",
        "--images-comment=Importing from https://example.com",
        "examplewiki",
    ], False)
    scripts = mwimport.get_scripts(args)
    assert scripts == [
        ["importDump", "dump.xml", "--no-updates"],
        ["importImages", "images", "--comment=Importing from https://example.com"],
        ["rebuildall"],
        ["initEditCount"],
        ["initSiteStats", "--update"],
    ]

def test_get_scripts_username_prefix():
    args = mwimport.parse_args([
        "--xml=dump.xml",
        "--username-prefix=w",
        "examplewiki",
    ], False)
    scripts = mwimport.get_scripts(args)
    assert scripts == [
        ["importDump", "dump.xml", "--no-updates", "--username-prefix=w"],
        ["rebuildall"],
        ["initEditCount"],
        ["initSiteStats", "--update"],
    ]

def test_get_scripts_search_recursively():
    args = mwimport.parse_args([
        "--images=images",
        "--images-comment=Importing from https://example.com",
        "--search-recursively",
        "examplewiki",
    ], False)
    scripts = mwimport.get_scripts(args)
    assert scripts == [
        ["importImages", "images", "--comment=Importing from https://example.com", "--search-recursively"],
        ["initSiteStats", "--update"],
    ]
