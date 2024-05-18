#! /usr/bin/python3

from miraheze.mediawiki import disable_puppet, enable_puppet
disable_puppet.disable_puppet()
input('press enter to re-enable puppet')
enable_puppet.enable_puppet()
