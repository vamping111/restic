%define buildid @BUILDID@

%bcond_without check
%define gobuild(o:) %{expand:
  # https://bugzilla.redhat.com/show_bug.cgi?id=995136#c12
  %global _dwz_low_mem_die_limit 0
  %ifnarch ppc64
  go build -buildmode pie -compiler gc -tags="rpm_crashtraceback ${BUILDTAGS:-}" -ldflags "${LDFLAGS:-}%{?currentgoldflags} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -extldflags '%__global_ldflags %{?__golang_extldflags}' -compressdwarf=false" -a -v -x %{?**};
  %else
  go build                -compiler gc -tags="rpm_crashtraceback ${BUILDTAGS:-}" -ldflags "${LDFLAGS:-}%{?currentgoldflags} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n') -extldflags '%__global_ldflags %{?__golang_extldflags}' -compressdwarf=false" -a -v -x %{?**};
  %endif
}

%define gometa(u:spvi) %{expand:%{lua:
local forgeurl    = rpm.expand("%{?-u*}")
if (forgeurl == "") then
	forgeurl        = rpm.expand("%{?forgeurl}")
end
-- Be explicit about the spec variables we’re setting
local function explicitset(rpmvariable,value)
	rpm.define(rpmvariable .. " " .. value)
	if (rpm.expand("%{?-v}") ~= "") then
	rpm.expand("%{echo:Setting %%{" .. rpmvariable .. "} = " .. value .. "\\n}")
	end
end
-- Never ever stomp on a spec variable the packager already set
local function safeset(rpmvariable,value)
	if (rpm.expand("%{?" .. rpmvariable .. "}") == "") then
	explicitset(rpmvariable,value)
	end
end
-- All the Go packaging automation relies on goipath being set
local goipath = rpm.expand("%{?goipath}")
if (goipath == "") then
	rpm.expand("%{error:Please set the Go import path in the “goipath” variable before calling “gometa”!}")
end
-- Compute and set spec variables
if (forgeurl ~= "") then
	rpm.expand("%forgemeta %{?-v} %{?-i} %{?-s} %{?-p} -u " .. forgeurl .. "\\n")
	safeset("gourl", forgeurl)
else
	safeset("gourl", "https://" .. goipath)
	rpm.expand("%forgemeta %{?-v} %{?-i} -s     %{?-p} %{gourl}\\n")
end
if (rpm.expand("%{?forgesource}") ~= "") then
	safeset("gosource", "%{forgesource}")
else
	safeset("gosource", "%{gourl}/%{archivename}.%{archiveext}")
end
safeset("goname", "%gorpmname %{goipath}")
-- Final spec variable summary if the macro was called with -i
if (rpm.expand("%{?-i}") ~= "") then
	rpm.expand("%{echo:Go-specific packaging variables}")
	rpm.expand("%{echo:  goipath:         %{?goipath}}")
	rpm.expand("%{echo:  goname:          %{?goname}}")
	rpm.expand("%{echo:  gourl:           %{?gourl}}")
	rpm.expand("%{echo:  gosource:        %{?gosource}}")
end}
}


# https://github.com/restic/restic
%global goipath         github.com/restic/restic
Version:                0.15.1

%gometa

%global common_description %{expand:
A backup program that is easy, fast, verifiable, secure, efficient and free.

Backup destinations can be:
*Local
*SFTP
*REST Server
*Amazon S3
*Minio Server
*OpenStack Swift
*Backblaze B2
*Microsoft Azure Blob Storage
*Google Cloud Storage
*Other Services via rclone}

%global golicenses    LICENSE


Name:    restic
Release: ROCKIT4%{buildid}%{?dist}
Summary: Fast, secure, efficient backup program
URL:     %{gourl}
License: BSD
Source0: %{name}-%{version}.tar.gz

ExcludeArch: s390x
BuildRequires: golang >= 1.18.0
BuildRequires: golang < 1.20

%description
%{common_description}

%prep
%autosetup -p1 -n %{name}-%{version}
%setup -q -T -D -n %{name}-%{version}


%build
%if 0%{?redos} == 8
export LDFLAGS=""
export CFLAGS=""
export CGO_CFLAGS=""
export CGO_LDFLAGS=""
%endif
export GO111MODULE=on
export GOFLAGS=-mod=vendor
%gobuild -o %{gobuilddir}/bin/%{name} %{goipath}/cmd/restic


%install
mkdir -p %{buildroot}%{_mandir}/man1
mkdir -p %{buildroot}%{_datarootdir}/zsh/site-functions
mkdir -p %{buildroot}%{_datarootdir}/bash-completion/completions
install -p -m 644 doc/man/* %{buildroot}%{_mandir}/man1/
#zsh completion
install -p -m 644 doc/zsh-completion.zsh %{buildroot}%{_datarootdir}/zsh/site-functions/_restic
#Bash completion
install -p -m 644 doc/bash-completion.sh %{buildroot}%{_datarootdir}/bash-completion/completions/restic
install -m 0755 -vd %{buildroot}%{_bindir}
install -p -m 755 %{gobuilddir}/bin/%{name} %{buildroot}%{_bindir}


%files
%license LICENSE
%doc GOVERNANCE.md CONTRIBUTING.md CHANGELOG.md README.md
%{_bindir}/%{name}
%dir %{_datadir}/zsh/site-functions
%{_datadir}/zsh/site-functions/_restic
%dir %{_datadir}/bash-completion/
%dir %{_datadir}/bash-completion/completions
%{_datadir}/bash-completion/completions/restic
%{_mandir}/man1/restic*.*


%changelog
* Mon Feb 13 2023 Aleksandr Rudenko <a.rudikk@gmail.com> - 0.15.1-1
- Initial package build for CROC Cloud
