import os
import tempfile
import pytest
from miraheze.mediawiki import mwimport


def test_parse_args_xml_images():
    args = mwimport.parse_args([
        '--xml=dump.xml',
        '--images=images',
        '--images-comment=Importing from https://example.com',
        'examplewiki',
    ], False)
    assert args.xml == 'dump.xml'
    assert args.images == 'images'
    assert args.images_comment == 'Importing from https://example.com'
    assert args.wiki == 'examplewiki'


def test_parse_args_images_recursively():
    args = mwimport.parse_args([
        '--images=images',
        '--search-recursively',
        '--images-comment=Importing from https://example.com',
        'examplewiki',
    ], False)
    assert args.images == 'images'
    assert args.search_recursively
    assert args.images_comment == 'Importing from https://example.com'
    assert args.wiki == 'examplewiki'


def test_parse_args_no_log_and_confirm_and_version():
    args = mwimport.parse_args([
        '--no-log',
        '--confirm',
        '--version=0.42',
        '--xml=dump.xml',
        'examplewiki',
    ], False)
    assert args.nolog
    assert args.confirm
    assert args.version == '0.42'


def test_parse_args_username_prefix():
    args = mwimport.parse_args([
        '--xml=dump.xml',
        '--username-prefix=w',
        'examplewiki',
    ], False)
    assert args.username_prefix == 'w'


def test_parse_args_need_xml_or_images():
    with pytest.raises(ValueError, match='--xml and/or --images must be passed'):
        mwimport.parse_args([
            'examplewiki',
        ])


def test_parse_args_images_need_comment():
    with pytest.raises(ValueError, match='--images-comment must be passed when importing images'):
        mwimport.parse_args([
            '--images=images',
            'examplewiki',
        ])


def test_parse_args_missing_xml():
    with pytest.raises(ValueError, match="Cannot find XML to import: '/dev/no xml'"):
        mwimport.parse_args([
            '--xml=/dev/no xml',
            'examplewiki',
        ])


def test_parse_args_missing_images():
    with pytest.raises(ValueError, match="Cannot find images to import: '/dev/no images'"):
        mwimport.parse_args([
            '--images=/dev/no images',
            '--images-comment=Importing from https://example.com',
            'examplewiki',
        ])


def test_parse_args_both_xml_images_exists():
    with tempfile.TemporaryDirectory() as tempdir:
        xml = os.path.join(tempdir, 'dump.xml')
        open(xml, 'w').close()

        images = os.path.join(tempdir, 'images')
        os.mkdir(images)

        args = mwimport.parse_args([
            f'--xml={xml}',
            f'--images={images}',
            '--images-comment=Importing from https://example.com',
            'examplewiki',
        ])

    assert args.xml == xml
    assert args.images == images


def test_get_scripts_xml_images():
    args = mwimport.parse_args([
        '--version=0.42',
        '--xml=dump.xml',
        '--images=images',
        '--images-comment=Importing from https://example.com',
        'examplewiki',
    ], False)
    scripts = mwimport.get_scripts(args)
    expected = [
        ['importDump', '--no-updates', '--', 'dump.xml'],
        ['importImages', '--comment=Importing from https://example.com', '--', 'images'],
        ['rebuildall'],
        ['initEditCount'],
        ['initSiteStats', '--update'],
    ]
    expected = [
        ['sudo', '-u', 'www-data', 'php', '/srv/mediawiki/0.42/maintenance/run.php', script[0], '--wiki=examplewiki', *script[1:]] for script in expected
    ]
    assert scripts == expected


def test_get_scripts_username_prefix():
    args = mwimport.parse_args([
        '--version=0.42',
        '--xml=dump.xml',
        '--username-prefix=w',
        'examplewiki',
    ], False)
    scripts = mwimport.get_scripts(args)
    expected = [
        ['importDump', '--no-updates', '--username-prefix=w', '--', 'dump.xml'],
        ['rebuildall'],
        ['initEditCount'],
        ['initSiteStats', '--update'],
    ]
    expected = [
        ['sudo', '-u', 'www-data', 'php', '/srv/mediawiki/0.42/maintenance/run.php', script[0], '--wiki=examplewiki', *script[1:]] for script in expected
    ]
    assert scripts == expected


def test_get_scripts_search_recursively():
    args = mwimport.parse_args([
        '--version=0.42',
        '--images=images',
        '--images-comment=Importing from https://example.com',
        '--search-recursively',
        'examplewiki',
    ], False)
    scripts = mwimport.get_scripts(args)
    expected = [
        ['importImages', '--comment=Importing from https://example.com', '--search-recursively', '--', 'images'],
        ['initSiteStats', '--update'],
    ]
    expected = [
        ['sudo', '-u', 'www-data', 'php', '/srv/mediawiki/0.42/maintenance/run.php', script[0], '--wiki=examplewiki', *script[1:]] for script in expected
    ]
    assert scripts == expected
