
%define veryoldname junkbust
%define oldname junkbuster
%define privoxyconf %{_sysconfdir}/%{name}
%define privoxy_uid 73
%define privoxy_gid 73

Name:		privoxy
Version:	3.0.0
Release:	1
Summary:	Privoxy - privacy enhancing proxy
License:	GPL
Source0:	http://www.waldherr.org/%{name}/%{name}-%{version}.tar.gz
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)
Group:		Networking/Daemons
URL:		http://www.privoxy.org/
Obsoletes:	junkbuster-raw junkbuster-blank junkbuster
# Prereq: /usr/sbin/useradd , /sbin/chkconfig , /sbin/service
Prereq:		shadow-utils, chkconfig, initscripts, sh-utils
BuildRequires:	perl gzip sed libtool autoconf lynx
Conflicts:	junkbuster-raw junkbuster-blank junkbuster

%description
Privoxy is a web proxy with advanced filtering capabilities for
protecting privacy, filtering web page content, managing cookies,
controlling access, and removing ads, banners, pop-ups and other
obnoxious Internet junk. Privoxy has a very flexible configuration and
can be customized to suit individual needs and tastes. Privoxy has
application for both stand-alone systems and multi-user networks.

Privoxy is based on the Internet Junkbuster.

%prep
%setup -q -c

%build

autoheader
autoconf
%configure --disable-dynamic-pcre
%{__make}

#strip %{name}

%install
rm -rf $RPM_BUILD_ROOT

[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}
install -d %{buildroot}%{_sbindir} \
         %{buildroot}%{_mandir}/man1 \
         %{buildroot}%{_localstatedir}/log/%{name} \
         %{buildroot}%{privoxyconf}/templates \
         %{buildroot}%{_sysconfdir}/logrotate.d \
         %{buildroot}%{_sysconfdir}/rc.d/init.d

install -s -m 744 %{name} %{buildroot}%{_sbindir}/%{name}

# Using sed to "convert" from DOS format to UNIX
# This is important behaviour, and should not be removed without some
# other assurance that these files don't get packed in the the
# wrong format
for i in `ls *.action`
do
       cat $i | sed -e 's/[[:cntrl:]]*$//' > %{buildroot}%{privoxyconf}/$i
done
cat default.filter | sed -e 's/[[:cntrl:]]*$//' > %{buildroot}%{privoxyconf}/default.filter
cat trust | sed -e 's/[[:cntrl:]]*$//' > %{buildroot}%{privoxyconf}/trust
(
cd templates
for i in `ls`
do
	cat $i | sed -e 's/[[:cntrl:]]*$//' > %{buildroot}%{privoxyconf}/templates/$i
done
)

cp -f %{name}.1 %{buildroot}%{_mandir}/man1/%{name}.1
cp -f %{name}.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
install -m 755 %{name}.init %{buildroot}%{_sysconfdir}/rc.d/init.d/%{name}
install -m 711 -d %{buildroot}%{_localstatedir}/log/%{name}

# verify all file locations, etc. in the config file
# don't start with ^ or commented lines are not replaced
## Changing the sed paramter delimiter to @, so we don't have to
## escape the slashes
cat config | \
    sed 's@^confdir.*@confdir %{privoxyconf}@g' | \
#    sed 's/^permissionsfile.*/permissionsfile \/etc\/%{name}\/permissionsfile/g' | \
#    sed 's/^filterfile.*/default.filter \/etc\/%{name}\/default.filter/g' | \
#    sed 's/^logfile.*/logfile \%{_localstatedir}\/log\/%{name}\/logfile/g' | \
#    sed 's/^jarfile.*/jarfile \%{_localstatedir}\/log\/%{name}\/jarfile/g' | \
#    sed 's/^forward.*/forward \/etc\/%{name}\/forward/g' | \
#    sed 's/^aclfile.*/aclfile \/etc\/%{name}\/aclfile/g' > \
    sed 's@^logdir.*@logdir %{_localstatedir}/log/%{name}@g' | \
    sed -e 's/[[:cntrl:]]*$//' > \
    %{buildroot}%{privoxyconf}/config
perl -pe 's/{-no-cookies}/{-no-cookies}\n\.redhat.com/' default.action >\
    %{buildroot}%{privoxyconf}/default.action


## Macros are expanded even on commentaries. So, we have to use %%
## -- morcego
#%%makeinstall

%pre
# This is where we handle old usernames (junkbust and junkbuster)
# I'm not sure we should do that, but this is the way we have been
# doing it for some time now -- morcego
# We should do it for the group as well -- morcego
# Doing it by brute force. Much cleaner (no more Mr. Nice Guy) -- morcego

# Same for username
usermod -u %{privoxy_uid} -g %{privoxy_gid} -l %{name} -d %{_sysconfdir}/%{name} -s "" %{oldname} > /dev/null 2>&1 || :
usermod -u %{privoxy_uid} -g %{privoxy_gid} -l %{name} -d %{_sysconfdir}/%{name} -s "" %{veryoldname} > /dev/null 2>&1 || :
userdel %{oldname} > /dev/null 2>&1 ||:
userdel %{veryoldname} > /dev/null 2>&1 ||:

# Change the group name. Remove anything left behind.
groupmod -g %{privoxy_gid} -n %{name} %{oldname} > /dev/null 2>&1 ||:
groupmod -g %{privoxy_gid} -n %{name} %{veryoldname} > /dev/null 2>&1 ||:
groupdel %{oldname} > /dev/null 2>&1 ||:
groupdel %{veryoldname} > /dev/null 2>&1 ||:

# Doublecheck to see if the group exist, and that it has the correct gid
/bin/grep -E '^%{name}:' %{_sysconfdir}/group > /dev/null 2>&1
if [ $? -eq 1 ]; then
	# Looks like it does not exist. Create it
	groupadd -g %{privoxy_gid} %{name} > /dev/null 2>&1
else
	/bin/grep -E '^%{name}:[^:]*:%{privoxy_gid}:' %{_sysconfdir}/group > /dev/null 2>&1
	if [ $? -eq 1 ]; then
		# The group exists, but does not have the correct gid
		groupmod -g %{privoxy_gid} %{name} > /dev/null 2>&1
	fi
fi

# Check to see if everything is okey. Create user if it still does not
# exist
id %{name} > /dev/null 2>&1
if [ $? -eq 1 ]; then
	%{_sbindir}/useradd -u %{privoxy_uid} -g %{privoxy_gid} -d %{_sysconfdir}/%{name} -r -s "" %{name} > /dev/null 2>&1
fi

# Double check that the group has the correct uid
P_UID=`id -u %{name} 2>/dev/null`
if [ $P_UID -ne %{privoxy_uid} ]; then
	%{_sbindir}/usermod -u %{privoxy_uid} %{name}
fi

# The same for the gid
P_GID=`id -g %{name} 2>/dev/null`
if [ $P_GID -ne %{privoxy_gid} ]; then
	%{_sbindir}/usermod -g %{privoxy_gid} %{name}
fi

%post
# for upgrade from 2.0.x
[ -f %{_localstatedir}/log/%{oldname}/logfile ] && {
  mv -f %{_localstatedir}/log/%{oldname}/logfile %{_localstatedir}/log/%{name}/logfile ||: ;
  chown -R %{name}:%{name} %{_localstatedir}/log/%{name} 2>/dev/null ||: ;
}
[ -f %{_localstatedir}/log/%{name}/%{name} ] && {
  mv -f %{_localstatedir}/log/%{name}/%{name} %{_localstatedir}/log/%{name}/logfile ||: ;
  chown -R %{name}:%{name} %{_sysconfdir}/%{name} 2>/dev/null ||: ;
}
/sbin/chkconfig --add privoxy
if [ "$1" = "1" ]; then
	/sbin/service %{name} condrestart > /dev/null 2>&1 ||:
fi

%preun
/sbin/service %{veryoldname} stop > /dev/null 2>&1 ||:
/sbin/service %{oldname} stop > /dev/null 2>&1 ||:

if [ "$1" = "0" ]; then
	/sbin/service %{name} stop > /dev/null 2>&1 ||:
	/sbin/chkconfig --del privoxy
fi

%postun
#if [ "$1" -ge "1" ]; then
#	/sbin/service %{name} condrestart > /dev/null 2>&1
#fi
# We only remove it we this is not an upgrade
if [ "$1" = "0" ]; then
	id privoxy > /dev/null 2>&1 && %{_sbindir}/userdel privoxy || /bin/true
	/bin/grep -E '^%{name}:' %{_sysconfdir}/group > /dev/null && %{_sbindir}/groupdel %{name} || /bin/true
fi

%clean
[ "%{buildroot}" != "/" ] && rm -rf %{buildroot}

%files
%defattr(644,root,root,755)
%doc README AUTHORS ChangeLog LICENSE
%doc doc/text/developer-manual.txt doc/text/user-manual.txt doc/text/faq.txt
%doc doc/webserver/developer-manual
%doc doc/webserver/user-manual
%doc doc/webserver/faq
%doc doc/webserver/p_doc.css doc/webserver/p_web.css doc/webserver/privoxy-index.html
%doc doc/webserver/images
%doc doc/webserver/man-page

# ATTENTION FOR defattr change here !
%defattr(0644,%{name},%{name},0755)

%dir %{privoxyconf}
%dir %{privoxyconf}/templates
%dir %{_localstatedir}/log/%{name}

%attr(0744,%{name},%{name})%{_sbindir}/%{name}

# WARNING ! WARNING ! WARNING ! WARNING ! WARNING ! WARNING ! WARNING !
# We should not use wildchars here. This could mask missing files problems
# -- morcego
# WARNING ! WARNING ! WARNING ! WARNING ! WARNING ! WARNING ! WARNING !
%config(noreplace) %{privoxyconf}/config
%config %{privoxyconf}/standard.action
%config(noreplace) %{privoxyconf}/user.action
%config %{privoxyconf}/default.action
%config %{privoxyconf}/default.filter
%config %{privoxyconf}/trust

# Please keep these alphabetized so its easier to find one that
# is not included.
%config %{privoxyconf}/templates/blocked
%config %{privoxyconf}/templates/cgi-error-404
%config %{privoxyconf}/templates/cgi-error-bad-param
%config %{privoxyconf}/templates/cgi-error-disabled
%config %{privoxyconf}/templates/cgi-error-file
%config %{privoxyconf}/templates/cgi-error-file-read-only
%config %{privoxyconf}/templates/cgi-error-modified
%config %{privoxyconf}/templates/cgi-error-parse
%config %{privoxyconf}/templates/cgi-style.css
%config %{privoxyconf}/templates/connect-failed
%config %{privoxyconf}/templates/default
%config %{privoxyconf}/templates/edit-actions-add-url-form
%config %{privoxyconf}/templates/edit-actions-for-url
%config %{privoxyconf}/templates/edit-actions-for-url-filter
%config %{privoxyconf}/templates/edit-actions-list
%config %{privoxyconf}/templates/edit-actions-list-button
%config %{privoxyconf}/templates/edit-actions-list-section
%config %{privoxyconf}/templates/edit-actions-list-url
%config %{privoxyconf}/templates/edit-actions-remove-url-form
%config %{privoxyconf}/templates/edit-actions-url-form
%config %{privoxyconf}/templates/mod-local-help
%config %{privoxyconf}/templates/mod-support-and-service
%config %{privoxyconf}/templates/mod-title
%config %{privoxyconf}/templates/mod-unstable-warning
%config %{privoxyconf}/templates/no-such-domain
%config %{privoxyconf}/templates/show-request
%config %{privoxyconf}/templates/show-status
%config %{privoxyconf}/templates/show-status-file
%config %{privoxyconf}/templates/show-url-info
%config %{privoxyconf}/templates/show-version
%config %{privoxyconf}/templates/toggle
%config %{privoxyconf}/templates/toggle-mini
%config %{privoxyconf}/templates/untrusted

# Attention, new defattr change here !
%defattr(0644,root,root,0755)

%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %attr(0755,root,root) %{_sysconfdir}/rc.d/init.d/%{name}

%{_mandir}/man1/%{name}.*

# $Log: privoxy.spec,v $
# Revision 1.1  2002-11-11 20:17:55  hunter
# --specfile taken from sf.net
#
# Revision 1.33.2.19  2002/08/25 23:36:03  hal9
# Bump version for 3.0.0.
#
# Revision 1.33.2.18  2002/08/10 11:28:50  oes
# Bumped version
#
# Revision 1.33.2.17  2002/08/07 01:08:49  hal9
# Bumped version to 2.9.18.
#
# Revision 1.33.2.16  2002/08/05 08:42:13  kick_
# same permissions, same runlevels as all the other initscripts
#
# Revision 1.33.2.15  2002/07/30 21:51:19  hal9
# Bump version to 2.9.17.
#
# Revision 1.33.2.14  2002/07/27 21:58:16  kick_
# bump version
#
# Revision 1.33.2.13  2002/07/27 21:39:41  kick_
# condrestart raised an error during an fresh install when privoxy wasn't already running
#
# Revision 1.33.2.12  2002/07/27 15:47:10  hal9
# Reset version and release for 2.9.16.
#
# Revision 1.33.2.11  2002/07/25 09:47:57  kick_
# this caused some errors during a fresh installation. It's unnecessary to call an extra program (/bin/true) to set the error code to 0
#
# Revision 1.33.2.10  2002/07/12 09:14:26  kick_
# don't use ghost files for rcX.d/*, chkconfig is available to do this job. Enable translation of error messge
#
# Revision 1.33.2.9  2002/07/05 17:16:19  morcego
# - Changing delete order for groups and users (users should be first)
#
# Revision 1.33.2.8  2002/07/03 20:46:24  morcego
# - Changing sed expression that removed CR from the end of the lines. This
#   new one removes any control caracter, and should work with older versions
#   of sed
#
# Revision 1.33.2.7  2002/07/02 18:16:48  morcego
# - Fixing defattr values. File and directory modes where swapped
#
# Revision 1.33.2.6  2002/07/02 17:38:10  morcego
# Bumping Release number
#
# Revision 1.33.2.5  2002/07/02 11:43:20  hal9
# Fix typo in templates creation.
#
# Revision 1.33.2.4  2002/06/26 17:32:45  morcego
# Integrating fixed from the main branch.
#
# Revision 1.33.2.3  2002/06/24 12:13:34  kick_
# shut up rpmlint. btw: The vendor tag should be set in you .rpmmacros file, not in the spec file!
#
# Revision 1.33.2.2  2002/05/28 02:39:38  hal9
# Replace index.html with privoxy-index.html for docs.
#
# Revision 1.33.2.1  2002/05/26 17:20:23  hal9
# Add images to doc dirs.
#
# Revision 1.33  2002/05/25 02:08:23  hal9
# Add doc/images directory.
# Redhat: alphabetized list of templates (and I think added one in the process)
#
# Revision 1.32  2002/05/16 01:37:29  hal9
# Add new template file so CGI stuff works :)
#
# Revision 1.31  2002/05/03 17:14:35  morcego
# *.spec: Version bump to 2.9.15
# -rh.spec: noreplace for %%{privoxyconf}/config
#           Will interrupt the build if versions from configure.in and
# 		specfile do not match
#
# Revision 1.30  2002/04/26 15:51:05  morcego
# Changing Vendor value to Privoxy.Org
#
# Revision 1.29  2002/04/24 03:13:51  hal9
# New actions files changes.
#
# Revision 1.28  2002/04/22 18:51:33  morcego
# user and group now get removed on rh too.
#
# Revision 1.27  2002/04/22 16:32:31  morcego
# configure.in, *.spec: Bumping release to 2 (2.9.14-2)
# -rh.spec: uid and gid are now macros
# -suse.spec: Changing the header Copyright to License (Copyright is
#             deprecable)
#
# Revision 1.26  2002/04/22 16:24:36  morcego
# - Changes to fixate the uid and gid values as (both) 73. This is a
#   value we hope to standarize for all distributions. RedHat already
#   uses it, and Conectiva should start as soon as I find where the heck
#   I left my cluebat :-)
# - Only remove the user and group on uninstall if this is not redhat, once
#   redhat likes to have the values allocated even if the package is not
#   installed
#
# Revision 1.25  2002/04/17 01:59:12  hal9
# Add --disable-dynamic-pcre.
#
# Revision 1.24  2002/04/11 10:09:20  oes
# Version 2.9.14
#
# Revision 1.23  2002/04/10 18:14:45  morcego
# - (privoxy-rh.spec only) Relisting template files on the %%files section
# - (configure.in, privoxy-rh.spec) Bumped package release to 5
#
# Revision 1.22  2002/04/09 22:06:12  hal9
# Remove 'make dok'.
#
# Revision 1.21  2002/04/09 02:52:26  hal9
# - Add templates/cgi-style.css, faq.txt, p_web.css, LICENSE
# - Remove templates/blocked-compact.
# - Add more docbook stuff to Buildrequires.
#
# Revision 1.20  2002/04/08 20:27:45  swa
# fixed JB spelling
#
# Revision 1.19  2002/03/27 22:44:59  sarantis
# Include correct documentation file.
#
# Revision 1.18  2002/03/27 22:10:14  sarantis
# bumped Hal's last commit 1 day to the future to make rpm build again.
#
# Revision 1.17  2002/03/27 00:48:23  hal9
# Fix up descrition.
#
# Revision 1.16  2002/03/26 22:29:55  swa
# we have a new homepage!
#
# Revision 1.15  2002/03/26 17:39:54  morcego
# Adding comment on the specfile to remember the packager to update
# the release number on the configure script
#
# Revision 1.14  2002/03/26 14:25:15  hal9
# Added edit-actions-for-url-filter to templates in %%config
#
# Revision 1.13  2002/03/25 13:31:04  morcego
# Bumping Release tag.
#
# Revision 1.12  2002/03/25 03:11:40  hal9
# Do it right way this time :/
#
# Revision 1.11  2002/03/25 03:09:51  hal9
# Added faq to docs.
#
# Revision 1.10  2002/03/24 22:16:14  morcego
# Just removing some old commentaries.
#
# Revision 1.9  2002/03/24 22:03:22  morcego
# Should be working now. See %changelog for details
#
# Revision 1.8  2002/03/24 21:13:01  morcego
# Tis broken.
#
# Revision 1.7  2002/03/24 21:07:18  hal9
# Add autoheader, etc.
#
# Revision 1.6  2002/03/24 19:56:40  hal9
# /etc/junkbuster is now /etc/privoxy. Fixed ';' typo.
#
# Revision 1.4  2002/03/24 13:32:42  swa
# name change related issues
#
# Revision 1.3  2002/03/24 12:56:21  swa
# name change related issues.
#
# Revision 1.2  2002/03/24 11:40:14  swa
# name change
#
# Revision 1.1  2002/03/24 11:23:44  swa
# name change
#
# Revision 1.1  2002/03/22 20:53:03  morcego
# - Ongoing process to change name to JunkbusterNG
# - configure/configure.in: no change needed
# - GNUmakefile.in:
#         - TAR_ARCH = /tmp/JunkbusterNG-$(RPM_VERSION).tar.gz
#         - PROGRAM    = jbng@EXEEXT@
#         - rh-spec now references as junkbusterng-rh.spec
#         - redhat-upload: references changed to junkbusterng-* (package names)
#         - tarball-dist: references changed to JunkbusterNG-distribution-*
#         - tarball-src: now JunkbusterNG-*
#         - install: initscript now junkbusterng.init and junkbusterng (when
#                    installed)
# - junkbuster-rh.spec: renamed to junkbusterng-rh.spec
# - junkbusterng.spec:
#         - References to the expression ijb where changed where possible
#         - New package name: junkbusterng (all in lower case, acording to
#           the LSB recomendation)
#         - Version changed to: 2.9.13
#         - Release: 1
#         - Added: junkbuster to obsoletes and conflicts (Not sure this is
#           right. If it obsoletes, why conflict ? Have to check it later)
#         - Summary changed: Stefan, please check and aprove it
#         - Changes description to use the new name
#         - Sed string was NOT changed. Have to wait to the manpage to
#           change first
#         - Keeping the user junkbuster for now. It will require some aditional
#           changes on the script (scheduled for the next specfile release)
#         - Added post entry to move the old logfile to the new log directory
#         - Removing "chkconfig --add" entry (not good to have it automaticaly
#           added to the startup list).
#         - Added preun section to stop the service with the old name, as well
#           as remove it from the startup list
#         - Removed the chkconfig --del entry from the conditional block on
#           the preun scriptlet (now handled on the %files section)
# - junkbuster.init: renamed to junkbusterng.init
# - junkbusterng.init:
#         - Changed JB_BIN to jbng
#         - Created JB_OBIN with the old value of JB_BIN (junkbuster), to
#           be used where necessary (config dir)
#
# Aditional notes:
# - The config directory is /etc/junkbuster yet. Have to change it on the
# specfile, after it is changes on the code
# - The only files that got renamed on the cvs tree were the rh specfile and
# the init file. Some file references got changes on the makefile and on the
# rh-spec (as listed above)
#
# Revision 1.43  2002/03/21 16:04:10  hal9
# added ijb_docs.css to %doc
#
# Revision 1.42  2002/03/12 13:41:18  sarantis
# remove hard-coded "ijbswa" string in build phase
#
# Revision 1.41  2002/03/11 22:58:32  hal9
# Remove --enable-no-gifs
#
# Revision 1.39  2002/03/08 18:57:29  swa
# remove user junkbuster after de-installation.
#
# Revision 1.38  2002/03/08 13:45:27  morcego
# Adding libtool to Buildrequires
#
# Revision 1.37  2002/03/07 19:23:49  swa
# i hate to scroll. suse: wrong configdir.
#
# Revision 1.36  2002/03/07 05:06:54  morcego
# Fixed %pre scriptlet. And, as a bonus, you can even understand it now. :-)
#
# Revision 1.34  2002/03/07 00:11:57  morcego
# Few changes on the %pre and %post sections of the rh specfile to handle
# usernames more cleanly
#
# Revision 1.33  2002/03/05 13:13:57  morcego
# - Added "make redhat-dok" to the build phase
# - Added docbook-utils to BuildRequires
#
# Revision 1.32  2002/03/05 12:34:24  morcego
# - Changing section internaly on the manpage from 1 to 8
# - We now require packages, not files, to avoid issues with apt
#
# Revision 1.31  2002/03/04 18:06:09  morcego
# SPECFILE: fixing permissing of the init script (broken by the last change)
#
# Revision 1.30  2002/03/04 16:18:03  morcego
# General cleanup of the rh specfile.
#
# %changelog
# * Mon Mar 04 2002 Rodrigo Barbosa <rodrigob@tisbrasil.com.br>
# + junkbuster-2.9.11-2
# - General specfile fixup, using the best recomended practices, including:
#         - Adding -q to %%setup
#         - Using macros whereever possible
#         - Not using wildchars on %%files section
#         - Doubling the percentage char on changelog and comments, to
#           avoid rpm expanding them
#
# Revision 1.29  2002/03/03 19:21:22  hal9
# Init script fails if shell is /bin/false.
#
# Revision 1.28  2002/01/09 18:34:03  hal9
# nit.
#
# Revision 1.27  2002/01/09 18:32:02  hal9
# Removed RPM_OPT_FLAGS kludge.
#
# Revision 1.26  2002/01/09 18:21:10  hal9
# A few minor updates.
#
# Revision 1.25  2001/12/28 01:45:36  steudten
# Add paranoia check and BuildReq: gzip
#
# Revision 1.24  2001/12/01 21:43:14  hal9
# Allowed for new ijb.action file.
#
# Revision 1.23  2001/11/06 12:09:03  steudten
# Compress doc files. Install README and AUTHORS at last as document.
#
# Revision 1.22  2001/11/05 21:37:34  steudten
# Fix to include the actual version for name.
# Let the 'real' packager be included - sorry stefan.
#
# Revision 1.21  2001/10/31 19:27:27  swa
# consistent description. new name for suse since
# we had troubles with rpms of identical names
# on the webserver.
#
# Revision 1.20  2001/10/24 15:45:49  hal9
# To keep Thomas happy (aka correcting my  mistakes)
#
# Revision 1.19  2001/10/15 03:23:59  hal9
# Nits.
#
# Revision 1.17  2001/10/10 18:59:28  hal9
# Minor change for init script.
#
# Revision 1.16  2001/09/24 20:56:23  hal9
# Minor changes.
#
# Revision 1.13  2001/09/10 17:44:43  swa
# integrate three pieces of documentation. needs work.
# will not build cleanly under redhat.
#
# Revision 1.12  2001/09/10 16:25:04  swa
# copy all templates. version updated.
#
# Revision 1.11  2001/07/03 11:00:25  sarantis
# replaced permissionsfile with actionsfile
#
# Revision 1.10  2001/07/03 09:34:44  sarantis
# bumped up version number.
#
# Revision 1.9  2001/06/12 18:15:29  swa
# the %% in front of configure (see tag below) confused
# the rpm build process on 7.1.
#
# Revision 1.8  2001/06/12 17:15:56  swa
# fixes, because a clean build on rh6.1 was impossible.
# GZIP confuses make, %% configure confuses rpm, etc.
#
# Revision 1.7  2001/06/11 12:17:26  sarantis
# fix typo in %%post
#
# Revision 1.6  2001/06/11 11:28:25  sarantis
# Further optimizations and adaptations in the spec file.
#
# Revision 1.5  2001/06/09 09:14:11  swa
# shamelessly adapted RPM stuff from the newest rpm that
# RedHat provided for the JB.
#
# Revision 1.4  2001/06/08 20:54:18  swa
# type with status file. remove forward et. al from file list.
#
# Revision 1.3  2001/06/07 17:28:10  swa
# cosmetics
#
# Revision 1.2  2001/06/04 18:31:58  swa
# files are now prefixed with either `confdir' or `logdir'.
# `make redhat-dist' replaces both entries confdir and logdir
# with redhat values
#
# Revision 1.1  2001/06/04 10:44:57  swa
# `make redhatr-dist' now works. Except for the paths
# in the config file.
#
#
#
