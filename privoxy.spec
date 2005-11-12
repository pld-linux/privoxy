Summary:	Privoxy - privacy enhancing proxy
Summary(pl):	Privoxy - proxy rozszerzaj±ce prywatno¶æ
Name:		privoxy
Version:	3.0.3
Release:	2.1
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
Privoxy to proxy WWW z rozszerzonymi mo¿liwo¶ciami filtrowania
s³u¿±cymi do zabezpieczenia prywatno¶ci, filtrowania zawarto¶ci stron
WWW, zarz±dzania ciasteczkami, kontroli dostêpu, usuwania bannerów,
wyskakuj±cych okienek i innych wstrêtnych internetowych ¶mieci.
Privoxy ma bardzo elastyczn± konfiguracjê i mo¿e byæ dopasowywane do
indywidualnych potrzeb i gustów. Privoxy ma aplikacjê dla systemów
samodzielnych i serwerów sieciowych dla wielu u¿ytkowników.

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
	$RPM_BUILD_ROOT%{_sysconfdir}/%{name}/templates \
	$RPM_BUILD_ROOT/etc/{logrotate.d,rc.d/init.d} \
	$RPM_BUILD_ROOT/var/log/%{name}
	
install -m 744 %{name} $RPM_BUILD_ROOT%{_sbindir}/%{name}

# Using sed to "convert" from DOS format to UNIX
# This is important behaviour, and should not be removed without some
# other assurance that these files don't get packed in the the
# wrong format
for i in `ls *.action`
do
	sed -e 's/[[:cntrl:]]*$//' $i > $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/$i
done
sed -e 's/[[:cntrl:]]*$//' default.filter > $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/default.filter
sed -e 's/[[:cntrl:]]*$//' trust > $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/trust
(
cd templates
for i in `ls`
do
	sed -e 's/[[:cntrl:]]*$//' $i > $RPM_BUILD_ROOT%{_sysconfdir}/%{name}/templates/$i
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
	sed 's@^confdir.*@confdir %{_sysconfdir}/%{name}@g' | \
# sed 's/^permissionsfile.*/permissionsfile \/etc\/%{name}\/permissionsfile/g' | \
# sed 's/^filterfile.*/default.filter \/etc\/%{name}\/default.filter/g' | \
# sed 's/^logfile.*/logfile \/var\/log\/%{name}\/logfile/g' | \
# sed 's/^jarfile.*/jarfile \/var\/log\/%{name}\/jarfile/g' | \
# sed 's/^forward.*/forward \/etc\/%{name}\/forward/g' | \
# sed 's/^aclfile.*/aclfile \/etc\/%{name}\/aclfile/g' > \
	sed 's@^logdir.*@logdir %{_localstatedir}/log/%{name}@g' | \
		sed -e 's/[[:cntrl:]]*$//' > \
		$RPM_BUILD_ROOT%{_sysconfdir}/%{name}/config
	perl -pe 's/{-no-cookies}/{-no-cookies}\n\.redhat.com/' default.action >\
		$RPM_BUILD_ROOT%{_sysconfdir}/%{name}/default.action

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -g 108 privoxy
%useradd -u 108 -d %{_sysconfdir}/%{name} -s /bin/false -c "%{name} user" -g privoxy privoxy

%post
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

%dir %attr(751,privoxy,privoxy) /var/log/%{name}

%dir %attr(751,root,privoxy) %{_sysconfdir}/%{name}
%dir %attr(751,root,privoxy) %{_sysconfdir}/%{name}/templates
%attr(751,root,privoxy) %config(noreplace) %verify(not size mtime md5) %{_sysconfdir}/%{name}/config
%attr(751,root,privoxy) %config(noreplace) %verify(not size mtime md5) %{_sysconfdir}/%{name}/trust
%attr(751,root,privoxy) %config(noreplace) %verify(not size mtime md5) %{_sysconfdir}/%{name}/*.*
%attr(751,root,privoxy) %config(noreplace) %verify(not size mtime md5) %{_sysconfdir}/%{name}/templates/*
