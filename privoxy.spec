
%define		oldname junkbuster
%define		privoxyconf %{_sysconfdir}/%{name}

Summary:	Privoxy - privacy enhancing proxy
Summary(pl):	Privoxy - proxy rozszerzaj�ce prywatno��
Name:		privoxy
Version:	3.0.3
Release:	2
License:	GPL
Source0:	http://dl.sourceforge.net/ijbswa/%{name}-%{version}-2-stable.src.tar.gz
# Source0-md5:	d7f6c2fcb926e6110659de6e866b21e4
Source1:	%{name}.init
Source2:	%{name}.logrotate
Group:		Networking/Daemons
URL:		http://www.privoxy.org/
BuildRequires:	autoconf
BuildRequires:	libtool
BuildRequires:	lynx
BuildRequires:	perl-base
BuildRequires:	rpmbuild(macros) >= 1.231
PreReq:		rc-scripts
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires(post):	fileutils
Requires(post,preun):	/sbin/chkconfig
Requires(postun):	/usr/sbin/groupdel
Requires(postun):	/usr/sbin/userdel
Provides:	group(privoxy)
Provides:	user(privoxy)
Obsoletes:	junkbuster
Obsoletes:	junkbuster-blank
Obsoletes:	junkbuster-raw
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Privoxy is a web proxy with advanced filtering capabilities for
protecting privacy, filtering web page content, managing cookies,
controlling access, and removing ads, banners, pop-ups and other
obnoxious Internet junk. Privoxy has a very flexible configuration and
can be customized to suit individual needs and tastes. Privoxy has
application for both stand-alone systems and multi-user networks.

Privoxy is based on the Internet Junkbuster.

%description -l pl
Privoxy to proxy WWW z rozszerzonymi mo�liwo�ciami filtrowania
s�u��cymi do zabezpieczenia prywatno�ci, filtrowania zawarto�ci stron
WWW, zarz�dzania ciasteczkami, kontroli dost�pu, usuwania banner�w,
wyskakuj�cych okienek i innych wstr�tnych internetowych �mieci.
Privoxy ma bardzo elastyczn� konfiguracj� i mo�e by� dopasowywane do
indywidualnych potrzeb i gust�w. Privoxy ma aplikacj� dla system�w
samodzielnych i serwer�w sieciowych dla wielu u�ytkownik�w.

Privoxy jest oparte na Internet Junkbusterze.

%prep
%setup -qcT
tar xf %{SOURCE0} --strip-components=1

%build
%{__autoheader}
%{__autoconf}
%configure \
	--disable-dynamic-pcre

%{__make}

%install
rm -rf $RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT%{_sbindir} \
	$RPM_BUILD_ROOT%{_mandir}/man1 \
	$RPM_BUILD_ROOT/var/log/%{name} \
	$RPM_BUILD_ROOT%{privoxyconf}/templates \
	$RPM_BUILD_ROOT/etc/{logrotate.d,rc.d/init.d} \
	$RPM_BUILD_ROOT/var/log/%{name}
	
install -m 744 %{name} $RPM_BUILD_ROOT%{_sbindir}/%{name}

# Using sed to "convert" from DOS format to UNIX
# This is important behaviour, and should not be removed without some
# other assurance that these files don't get packed in the the
# wrong format
for i in `ls *.action`
do
	cat $i | sed -e 's/[[:cntrl:]]*$//' > $RPM_BUILD_ROOT%{privoxyconf}/$i
done
cat default.filter | sed -e 's/[[:cntrl:]]*$//' > $RPM_BUILD_ROOT%{privoxyconf}/default.filter
cat trust | sed -e 's/[[:cntrl:]]*$//' > $RPM_BUILD_ROOT%{privoxyconf}/trust
(
cd templates
for i in `ls`
do
	cat $i | sed -e 's/[[:cntrl:]]*$//' > $RPM_BUILD_ROOT%{privoxyconf}/templates/$i
done
)

cp -f %{name}.1 $RPM_BUILD_ROOT%{_mandir}/man1/%{name}.1
cp -f %{name}.logrotate $RPM_BUILD_ROOT/etc/logrotate.d/%{name}

install %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/%{name}
install %{SOURCE2} $RPM_BUILD_ROOT/etc/logrotate.d/%{name}

# verify all file locations, etc. in the config file
# don't start with ^ or commented lines are not replaced
## Changing the sed paramter delimiter to @, so we don't have to
## escape the slashes
cat config | \
	sed 's@^confdir.*@confdir %{privoxyconf}@g' | \
# sed 's/^permissionsfile.*/permissionsfile \/etc\/%{name}\/permissionsfile/g' | \
# sed 's/^filterfile.*/default.filter \/etc\/%{name}\/default.filter/g' | \
# sed 's/^logfile.*/logfile \/var\/log\/%{name}\/logfile/g' | \
# sed 's/^jarfile.*/jarfile \/var\/log\/%{name}\/jarfile/g' | \
# sed 's/^forward.*/forward \/etc\/%{name}\/forward/g' | \
# sed 's/^aclfile.*/aclfile \/etc\/%{name}\/aclfile/g' > \
	sed 's@^logdir.*@logdir %{_localstatedir}/log/%{name}@g' | \
		sed -e 's/[[:cntrl:]]*$//' > \
		$RPM_BUILD_ROOT%{privoxyconf}/config
	perl -pe 's/{-no-cookies}/{-no-cookies}\n\.redhat.com/' default.action >\
		$RPM_BUILD_ROOT%{privoxyconf}/default.action

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -g 108 privoxy
%useradd -u 108 -d %{privoxyconf} -s /bin/false -c "%{name} user" -g privoxy privoxy

%post
# for upgrade from 2.0.x
[ -f /var/log/%{oldname}/logfile ] && {
	mv -f /var/log/%{oldname}/logfile /var/log/%{name}/logfile ||: ;
	chown -R %{name}:%{name} /var/log/%{name} 2>/dev/null ||: ;
}
[ -f /var/log/%{name}/%{name} ] && {
	mv -f /var/log/%{name}/%{name} /var/log/%{name}/logfile ||: ;
	chown -R %{name}:%{name} %{privoxyconf} 2>/dev/null ||: ;
}
/sbin/chkconfig --add privoxy
%service privoxy restart

%preun
if [ "$1" = "0" ]; then
	%service -q privoxy stop
	/sbin/chkconfig --del privoxy
fi

%postun
if [ "$1" = "0" ]; then
	%userremove privoxy
	%groupremove privoxy
fi

%files
%defattr(644,root,root,755)
%doc AUTHORS ChangeLog README
%doc doc/text/developer-manual.txt doc/text/user-manual.txt doc/text/faq.txt
%doc doc/webserver/developer-manual
%doc doc/webserver/user-manual
%doc doc/webserver/faq
%doc doc/webserver/*.css doc/webserver/privoxy-index.html
%doc doc/webserver/images
%doc doc/webserver/man-page

%config(noreplace) %verify(not size mtime md5) /etc/logrotate.d/%{name}
%attr(754,root,root) /etc/rc.d/init.d/%{name}
%attr(755,root,root) %{_sbindir}/%{name}
%{_mandir}/man1/%{name}.*

# ATTENTION FOR defattr change here !
%defattr(644,%{name},%{name},755)
%dir %{privoxyconf}
%dir %{privoxyconf}/templates
%dir /var/log/%{name}

# WARNING ! WARNING ! WARNING ! WARNING ! WARNING ! WARNING ! WARNING !
# We should not use wildchars here. This could mask missing files problems
# -- morcego
# WARNING ! WARNING ! WARNING ! WARNING ! WARNING ! WARNING ! WARNING !
%config(noreplace) %verify(not size mtime md5) %{privoxyconf}/config
%config %{privoxyconf}/standard.action
%config(noreplace) %verify(not size mtime md5) %{privoxyconf}/user.action
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
