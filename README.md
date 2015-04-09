# Redomat -- Environment for reproducable building, integration, testing

## SYNOPSIS

Redomat is a tool which provides an environment for doing reproducable
builds, integration and testing of targets. A target usually is a
Linux based system designed for a special purpose.

Reproducability is achieved by employing Docker (including its Python-API
and GIT (including repo-tool), and Yocto for actually building.
The target specification is provided as XML file which may reference 
additional files. The declaration may define build-stages (like build 
milestones) which will be accessible as docker-commits/images.
Using a certain milestone when building makes sense for 
software-development to spare the time of a full rebuild but still have 
the same effect.


## DEPENDENCIES
* python
* virtualenv [homepage](https://virtualenv.pypa.io/)
* docker [homepage](www.docker.com)
* GNUmake

## How to install

```
make install
```

*redomat* gets installed into /usr/local per default; provide the DESTDIR
variable to change the default location.

## How to use
To use Redomat to build a target from a declaration, execute:

```
redomat <REDOMAT.XML>
```

Optionally you can specify a stage/milestone from a previous
build (BUILDID) as a starting point for the build:

```
redomat -e <STAGE> -b <BUILDID> <REDOMAT.XML>
```

## How to serve build artifacts

The result of a build is what we call build artifacts. Build
artifacts can be build logs, filesystem images, packages and
more. It is possible to serve these build artifacts via the
Docker container used for building:

```
docker run --rm -ti -d -p <hostport>:80 <IMAGE> /build/serve.sh
redomat.py --serve <BUILDID>
```

This will make the build artifacts accessible on `http://localhost:<hostport>`

## REDOMAT.XML reference guide

### To declare the Yocto layers 

Redomat uses repo-tool to checkout respective GIT revisions of different 
repositories, to form the used Yocto layers. The redomat XML nodes for this
are very similar to repo-tool XML-syntax:
```
  <layer_declaration>
    <remote fetch="REPO_URL" name="REPO_NAME" />
    <layer remote="REMOTE_NAME" revision="REPO_REVISION" reponame="REPO_URL" />
    <layer remote="REMOTE_NAME" revision="REPO_REVISION" reponame="REPO_URL" />
    <layer remote="REMOTE_NAME" revision="REPO_REVISION" reponame="REPO_URL" />
  </layer_declaration>
```

A bblayers.conf will be automatically generated from the declaration.

### To declare build stages use:
```
  <buildstage id='STAGE_NAME'>
    <prestage> STAGE_NAME </prestage>
    <dockerline> DOCKERFILE COMMAND </dockerline>
    <bitbake_target command="BITBAKE COMMAND"> BITBAKE_TARGET </bitbake_target> 
  <buildstage>
```

### to declare additional configuration:

Additional configuration can be put in the <local_conf> node
and will end up in a generated local.conf.

```
  <local_conf>
    <BB_NUMBER_THREADS>NUMBER OF CPU CORES</BB_NUMBER_THREADS>
    <PARALLEL_MAKE>NUMBER OF MAKE THEADS</PARALLEL_MAKE>
    <MACHINE>MACHINE</MACHINE>
    <DISTRO>DISTRO</DISTRO>
  </local_conf>
```

