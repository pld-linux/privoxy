Summary:	Privoxy - privacy enhancing proxy
Summary(pl.UTF-8):	Privoxy - proxy rozszerzające prywatność
Name:		privoxy
Version:	3.0.10
Release:	0.1
License:	GPL v2+
Source0:	http://dl.sourceforge.net/ijbswa/%{name}-%{version}-stable-src.tar.gz
# Source0-md5:	01281017f28be2c7133124d1768da364
Source1:	%{name}.init
Source2:	%{name}.logrotate
Group:		Networking/Daemons
URL:		http://www.privoxy.org/
BuildRequires:	autoconf
BuildRequires:	automake
BuildRequires:	libtool
BuildRequires:	lynx
BuildRequires:	pcre-devel
BuildRequires:	perl-base
BuildRequires:	rpmbuild(macros) >= 1.268
Requires(post):	fileutils
Requires(post,preun):	/sbin/chkconfig
Requires(postun):	/usr/sbin/groupdel
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires:	rc-scripts
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

%description -l pl.UTF-8
Privoxy to proxy WWW z rozszerzonymi możliwościami filtrowania
służącymi do zabezpieczenia prywatności, filtrowania zawartości stron
WWW, zarządzania ciasteczkami, kontroli dostępu, usuwania bannerów,
wyskakujących okienek i innych wstrętnych internetowych śmieci.
Privoxy ma bardzo elastyczną konfigurację i może być dopasowywane do
indywidualnych potrzeb i gustów. Privoxy ma aplikację dla systemów
samodzielnych i serwerów sieciowych dla wielu użytkowników.

Privoxy jest oparte na Internet Junkbusterze.

%prep
%setup -q -n %{name}-%{version}-stable

%build
%{__aclocal}
%{__autoconf}
%{__autoheader}
cp -f /usr/share/automake/config.sub .
%configure

%{__make} \
	CFLAGS="%{rpmcflags}"
# XXX: above supresses -pthread; should it be added?

%install
rm -rf $RPM_BUILD_ROOT

%{__make} install \
	CONF_BASE=%{_sysconfdir}/privoxy \
	DESTDIR=$RPM_BUILD_ROOT

install -D %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/%{name}
install -D %{SOURCE2} $RPM_BUILD_ROOT/etc/logrotate.d/%{name}

# just GPLv2
rm -f $RPM_BUILD_ROOT%{_docdir}/privoxy/LICENSE

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
%attr(755,root,root) %{_sbindir}/%{name}
%{_mandir}/man1/%{name}.*
%config(noreplace) %verify(not md5 mtime size) /etc/logrotate.d/%{name}
%attr(754,root,root) /etc/rc.d/init.d/%{name}

%dir %attr(751,privoxy,privoxy) /var/log/%{name}
%ghost %attr(640,privoxy,privoxy) %verify(not md5 mtime size) /var/log/%{name}/*

%dir %attr(751,root,privoxy) %{_sysconfdir}/%{name}
%dir %attr(751,root,privoxy) %{_sysconfdir}/%{name}/templates
%attr(640,root,privoxy) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/config
%attr(640,root,privoxy) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/trust
%attr(640,root,privoxy) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/*.*
%attr(640,root,privoxy) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/%{name}/templates/*

%doc $RPM_BUILD_ROOT%{_docdir}/%{name}/*
