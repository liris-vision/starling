#!/bin/bash
#
# STARLING PROJECT 
#
# LIRIS - Laboratoire d'InfoRmatique en Image et Systèmes d'information 
#
# Copyright: 2012 - 2015 Eric Lombardi (eric.lombardi@liris.cnrs.fr), LIRIS (liris.cnrs.fr), CNRS (www.cnrs.fr)
#
#
#    This program is free software: you can redistribute it and/or modify it
#    under the terms of the GNU General Public License version 3, as published
#    by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranties of
#    MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
#    PURPOSE.  See the GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    For further information, check the COPYING file distributed with this software.
#
#----------------------------------------------------------------------
#
# Make a debian binary package including Starling
# and public LIRIS-VISION modules
#

major_version="$(date +%y)"
minor_version="$(date +%m%d)"
package_name="starling_${major_version}.${minor_version}-1"
tmp_pkg_dir="/tmp/${package_name}"

target_starling_dir="/usr/local/starling_${major_version}.${minor_version}"
tmp_starling_dir="$tmp_pkg_dir/$target_starling_dir"

target_modules_dir="/usr/local/liris-vision-modules_${major_version}.${minor_version}"
tmp_modules_dir="$tmp_pkg_dir/$target_modules_dir"

install_instructions_file="$(readlink -fm "$tmp_pkg_dir/../$package_name.README")"


# export Starling local git repo content
rm -rf "$tmp_pkg_dir"
mkdir -p "$tmp_starling_dir"  &&  git archive master | tar -x -C "$tmp_starling_dir"
# create a symlink to starling.py in /usr/local/bin
mkdir "$tmp_pkg_dir/usr/local/bin"
ln -s "$target_starling_dir/starling.py" "$tmp_pkg_dir/usr/local/bin/starling"

# export vision modules from github
git clone --depth=1 https://github.com/liris-vision/modules.git "$tmp_modules_dir"  &&  rm -rf "$tmp_modules_dir/.git"

# create and populate the metadata file for dpkg
mkdir "$tmp_pkg_dir"/DEBIAN
echo "Package: starling
Version: ${major_version}.${minor_version}-1
Section: devel
Priority: optional
Architecture: all
Depends: libopencv-dev (>=2.4.8), libcv-dev (>=2.4.8), libhighgui-dev (>=2.4.8), libcvaux-dev (>=2.4.8), libavcodec-extra-54 (>=6:9.11), python-gnome2 (>=2.28.1), python-pyorbit (>=2.24.0), python-pygoocanvas (>=0.14.1), python-opencv (>=2.4.8), g++ (>=4:4.8.2), cmake (>=2.8.0)
Maintainer: https://github.com/liris-vision/starling
Description: Starling
 Starling is a graphical tool to build simple computer-vision applications.
 It provides an easy to use graphical environment to experiment computer vision, and to generate C++ code examples of vision algorithms use. It relies on the OpenCV library.
" > "$tmp_pkg_dir"/DEBIAN/control

# create postinst script
echo "#!/bin/bash
#
set -e
echo 'Compiling LIRIS-VISION modules provided with Starling ...'

cd "$target_modules_dir" && mkdir build && cd build
cmake -DSTARLING_DIR=$target_starling_dir ..
make
make install
echo 'Compiling LIRIS-VISION modules done.'

" > "$tmp_pkg_dir"/DEBIAN/postinst

chmod 755 "$tmp_pkg_dir"/DEBIAN/postinst

# create prerm script
echo "#!/bin/bash
#
set -e

# uninstall LIRIS-VISION modules
cd "$target_modules_dir"/build
make uninstall
cd "$target_modules_dir"

# remove LIRIS-VISION modules build
rm -rf "$target_modules_dir"/build
rm -rf "$target_modules_dir"/*/build

# remove extra Starling directories
rm -r $target_starling_dir/app_data/*.extra
rm -r $target_starling_dir/*.extra
" > "$tmp_pkg_dir"/DEBIAN/prerm

chmod 755 "$tmp_pkg_dir"/DEBIAN/prerm

# build package
fakeroot dpkg-deb --build "$tmp_pkg_dir"

# generate installation instructions
echo "
             How to install $package_name package


The easiest way to install the package and its dependencies is to use 'gdebi':
  $ sudo aptitude install gdebi-core
  $ sudo gdebi $package_name.deb
    # install package and dependencies

During installation some vision modules are compiled. All the files (from the package and compiled) are installed in '$target_starling_dir' and '$target_modules_dir' directories. 

The Starling application is started by the script '$target_starling_dir/starling.py'. A link is added in '/usr/local/bin', so that it is possible to simply run the command 'starling'.

To remove the package installed with gdebi:
  $ aptitude purge $package_name
" > "$install_instructions_file"

echo "Installation instructions in '$install_instructions_file'"

